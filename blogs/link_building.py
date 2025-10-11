# blogs/link_building.py
import re
import requests
from urllib.parse import urlparse, urljoin
from django.db import models
from django.utils.html import strip_tags
from django.urls import reverse
from collections import Counter, defaultdict
from bs4 import BeautifulSoup
import nltk
from textrank4zh import TextRank4Sentence
from django.contrib.contenttypes.models import ContentType
from .models import LinkOpportunity, BrokenLink, LinkPerformance  # Import from models


class AILinkBuilder:
    """AI-powered internal linking system"""
    
    def __init__(self):
        self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
        
    def analyze_content_for_links(self, blog_post, all_posts=None):
        """Analyze blog post content for internal linking opportunities"""
        if all_posts is None:
            from blogs.models import Blog
            all_posts = Blog.objects.filter(status='Published').exclude(id=blog_post.id)
        
        opportunities = []
        content = strip_tags(blog_post.blog_body)
        
        # Extract key phrases and entities
        key_phrases = self._extract_key_phrases(content)
        entities = self._extract_entities(content)
        
        for target_post in all_posts:
            # Calculate semantic similarity
            similarity_score = self._calculate_semantic_similarity(blog_post, target_post)
            
            if similarity_score > 0.3:  # Minimum relevance threshold
                # Find potential anchor texts
                anchor_opportunities = self._find_anchor_opportunities(
                    content, target_post, key_phrases, entities
                )
                
                for anchor_text, context, score in anchor_opportunities:
                    opportunities.append({
                        'target_post': target_post,
                        'anchor_text': anchor_text,
                        'context': context,
                        'relevance_score': similarity_score * score,
                        'target_url': target_post.get_absolute_url()
                    })
        
        # Sort by relevance score
        opportunities.sort(key=lambda x: x['relevance_score'], reverse=True)
        return opportunities[:10]  # Return top 10 opportunities
    
    def _extract_key_phrases(self, content):
        """Extract key phrases using TextRank algorithm"""
        try:
            tr4s = TextRank4Sentence()
            tr4s.analyze(content, lower=True, source='all_filters')
            
            # Get key sentences and extract phrases
            key_sentences = tr4s.get_key_sentences(num=5)
            
            phrases = []
            for sentence in key_sentences:
                # Extract noun phrases (simplified)
                words = sentence.sentence.split()
                for i in range(len(words) - 1):
                    if len(words[i]) > 3 and len(words[i+1]) > 3:
                        phrase = f"{words[i]} {words[i+1]}"
                        if phrase.lower() not in self.stop_words:
                            phrases.append(phrase)
            
            return list(set(phrases))[:20]
        except:
            # Fallback to simple extraction
            return self._simple_phrase_extraction(content)
    
    def _simple_phrase_extraction(self, content):
        """Simple phrase extraction as fallback"""
        sentences = content.split('.')
        phrases = []
        
        for sentence in sentences:
            words = sentence.split()
            # Extract 2-3 word phrases
            for i in range(len(words) - 1):
                if len(words[i]) > 3 and len(words[i+1]) > 3:
                    phrase = f"{words[i]} {words[i+1]}"
                    if not any(stop in phrase.lower() for stop in self.stop_words):
                        phrases.append(phrase)
        
        # Return most common phrases
        phrase_counts = Counter(phrases)
        return [phrase for phrase, count in phrase_counts.most_common(20)]
    
    def _extract_entities(self, content):
        """Extract named entities (simplified)"""
        # This is a simplified version - in production, use spaCy or NLTK
        entity_patterns = [
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Names
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Proper nouns
        ]
        
        entities = []
        for pattern in entity_patterns:
            matches = re.findall(pattern, content)
            entities.extend(matches)
        
        return list(set(entities))[:15]
    
    def _calculate_semantic_similarity(self, post1, post2):
        """Calculate semantic similarity between two posts"""
        # Extract content
        content1 = strip_tags(post1.blog_body).lower()
        content2 = strip_tags(post2.blog_body).lower()
        
        # Simple similarity based on common words and phrases
        words1 = set(content1.split())
        words2 = set(content2.split())
        
        # Remove stop words
        words1 = {word for word in words1 if word not in self.stop_words and len(word) > 3}
        words2 = {word for word in words2 if word not in self.stop_words and len(word) > 3}
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        jaccard_similarity = intersection / union if union > 0 else 0
        
        # Boost similarity if posts are in same category
        category_boost = 0.2 if post1.category == post2.category else 0
        
        # Boost similarity if posts share tags
        post1_tags = set(post1.tags.names())
        post2_tags = set(post2.tags.names())
        tag_similarity = len(post1_tags.intersection(post2_tags)) / max(len(post1_tags.union(post2_tags)), 1)
        
        total_similarity = jaccard_similarity + category_boost + (tag_similarity * 0.3)
        return min(total_similarity, 1.0)
    
    def _find_anchor_opportunities(self, content, target_post, key_phrases, entities):
        """Find potential anchor text opportunities"""
        opportunities = []
        
        # Check if target post title appears in content
        title_matches = self._find_title_mentions(content, target_post.title)
        for match, context in title_matches:
            opportunities.append((match, context, 1.0))
        
        # Check if target post's keywords appear in content
        if target_post.seo_keywords:
            keywords = [kw.strip() for kw in target_post.seo_keywords.split(',')]
            for keyword in keywords:
                keyword_matches = self._find_keyword_mentions(content, keyword)
                for match, context in keyword_matches:
                    opportunities.append((match, context, 0.8))
        
        # Check if target post's tags appear in content
        for tag in target_post.tags.all():
            tag_matches = self._find_keyword_mentions(content, tag.name)
            for match, context in tag_matches:
                opportunities.append((match, context, 0.6))
        
        # Check for semantic matches with extracted phrases
        target_content = strip_tags(target_post.blog_body).lower()
        for phrase in key_phrases:
            if phrase.lower() in target_content and phrase.lower() in content.lower():
                phrase_matches = self._find_keyword_mentions(content, phrase)
                for match, context in phrase_matches:
                    opportunities.append((match, context, 0.5))
        
        return opportunities
    
    def _find_title_mentions(self, content, title):
        """Find mentions of the target post's title in content"""
        mentions = []
        title_lower = title.lower()
        content_lower = content.lower()
        
        # Direct title match
        if title_lower in content_lower:
            start_idx = content_lower.find(title_lower)
            context = self._extract_context(content, start_idx, len(title))
            mentions.append((title, context))
        
        # Partial title matches (at least 3 words)
        title_words = title.split()
        if len(title_words) >= 3:
            for i in range(len(title_words) - 2):
                partial_title = ' '.join(title_words[i:i+3])
                if partial_title.lower() in content_lower:
                    start_idx = content_lower.find(partial_title.lower())
                    context = self._extract_context(content, start_idx, len(partial_title))
                    mentions.append((partial_title, context))
        
        return mentions
    
    def _find_keyword_mentions(self, content, keyword):
        """Find mentions of a keyword in content"""
        mentions = []
        keyword_lower = keyword.lower()
        content_lower = content.lower()
        
        # Find all occurrences
        start = 0
        while True:
            idx = content_lower.find(keyword_lower, start)
            if idx == -1:
                break
            
            # Check if it's a whole word match
            if (idx == 0 or not content_lower[idx-1].isalnum()) and \
               (idx + len(keyword_lower) >= len(content_lower) or not content_lower[idx + len(keyword_lower)].isalnum()):
                context = self._extract_context(content, idx, len(keyword))
                mentions.append((keyword, context))
            
            start = idx + 1
        
        return mentions
    
    def _extract_context(self, content, start_idx, length, context_length=200):
        """Extract context around a found phrase"""
        context_start = max(0, start_idx - context_length // 2)
        context_end = min(len(content), start_idx + length + context_length // 2)
        
        context = content[context_start:context_end]
        
        # Try to start and end on word boundaries
        if context_start > 0:
            space_idx = context.find(' ')
            if space_idx != -1:
                context = context[space_idx + 1:]
        
        if context_end < len(content):
            space_idx = context.rfind(' ')
            if space_idx != -1:
                context = context[:space_idx]
        
        return context.strip()
    
    def generate_link_suggestions(self, blog_post):
        """Generate comprehensive link suggestions"""
        suggestions = {
            'internal_links': self.analyze_content_for_links(blog_post),
            'broken_links': self.check_broken_links(blog_post),
            'anchor_optimization': self.analyze_anchor_texts(blog_post),
            'competitor_gaps': self.find_competitor_link_gaps(blog_post)
        }
        
        return suggestions
    
    def check_broken_links(self, blog_post):
        """Check for broken links in the post"""
        broken_links = []
        
        # Extract all links from the post content
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        links = re.findall(link_pattern, blog_post.blog_body, re.IGNORECASE)
        
        for url, anchor_text in links:
            try:
                # Skip relative URLs and anchors
                if url.startswith('#') or not url.startswith(('http://', 'https://')):
                    continue
                
                response = requests.head(url, timeout=10, allow_redirects=True)
                if response.status_code >= 400:
                    broken_links.append({
                        'url': url,
                        'anchor_text': anchor_text,
                        'status_code': response.status_code,
                        'error_message': f"HTTP {response.status_code}"
                    })
                    
                    # Save to database
                    content_type = ContentType.objects.get_for_model(blog_post)
                    BrokenLink.objects.get_or_create(
                        content_type=content_type,
                        object_id=blog_post.id,
                        url=url,
                        defaults={
                            'anchor_text': anchor_text,
                            'status_code': response.status_code,
                            'error_message': f"HTTP {response.status_code}"
                        }
                    )
                    
            except requests.exceptions.RequestException as e:
                broken_links.append({
                    'url': url,
                    'anchor_text': anchor_text,
                    'status_code': 0,
                    'error_message': str(e)
                })
        
        return broken_links
    
    def analyze_anchor_texts(self, blog_post):
        """Analyze and optimize anchor texts"""
        link_pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        links = re.findall(link_pattern, blog_post.blog_body, re.IGNORECASE)
        
        anchor_analysis = {
            'total_links': len(links),
            'internal_links': 0,
            'external_links': 0,
            'generic_anchors': 0,
            'keyword_anchors': 0,
            'suggestions': []
        }
        
        generic_anchors = ['click here', 'read more', 'here', 'this', 'link']
        
        for url, anchor_text in links:
            anchor_lower = anchor_text.lower().strip()
            
            # Categorize links
            if url.startswith(('http://', 'https://')):
                anchor_analysis['external_links'] += 1
            else:
                anchor_analysis['internal_links'] += 1
            
            # Check for generic anchors
            if anchor_lower in generic_anchors:
                anchor_analysis['generic_anchors'] += 1
                anchor_analysis['suggestions'].append({
                    'type': 'generic_anchor',
                    'current': anchor_text,
                    'suggestion': f'Replace "{anchor_text}" with descriptive text',
                    'url': url
                })
            
            # Check for keyword anchors
            if blog_post.focus_keyword and blog_post.focus_keyword.lower() in anchor_lower:
                anchor_analysis['keyword_anchors'] += 1
        
        # Generate optimization suggestions
        if anchor_analysis['generic_anchors'] > 0:
            anchor_analysis['suggestions'].append({
                'type': 'reduce_generic',
                'message': f'Replace {anchor_analysis["generic_anchors"]} generic anchor texts with descriptive ones'
            })
        
        if anchor_analysis['keyword_anchors'] == 0 and blog_post.focus_keyword:
            anchor_analysis['suggestions'].append({
                'type': 'add_keyword_anchor',
                'message': f'Consider adding an anchor text containing "{blog_post.focus_keyword}"'
            })
        
        return anchor_analysis
    
    def find_competitor_link_gaps(self, blog_post):
        """Identify competitor link opportunities (simplified)"""
        # This is a simplified version - in production, you'd use tools like Ahrefs API
        gaps = []
        
        # Analyze what competitors might be linking to based on content
        content_themes = self._extract_themes(blog_post)
        
        for theme in content_themes:
            gaps.append({
                'theme': theme,
                'opportunity': f'Create content about "{theme}" and build links around it',
                'potential_value': 'Medium'
            })
        
        return gaps[:5]
    
    def _extract_themes(self, blog_post):
        """Extract main themes from blog post"""
        content = strip_tags(blog_post.blog_body)
        
        # Simple theme extraction using most common meaningful words
        words = [word.lower() for word in content.split() 
                if len(word) > 4 and word.lower() not in self.stop_words]
        
        word_counts = Counter(words)
        themes = [word for word, count in word_counts.most_common(10) if count > 2]
        
        return themes

# Management command for link building analysis
# blogs/management/commands/analyze_links.py
