# blogs/ai_content.py
import re
import json
import nltk
#import ssl
from textstat import flesch_reading_ease, flesch_kincaid_grade
from collections import Counter
from django.utils.html import strip_tags
from django.conf import settings
import openai
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

# For production/deployment time
#try:
   # _create_unverified_https_context = ssl._create_unverified_context
#except AttributeError:
 #   pass
#else:
   # ssl._create_default_https_context = _create_unverified_https_context

#nltk.download('punkt_tab', quiet=True)

class AIContentIntelligence:
    """AI-powered content analysis and optimization system"""
    
    def __init__(self, blog_post):
        self.post = blog_post
        self.content = strip_tags(blog_post.blog_body)
        self.title = blog_post.title
        self.meta_description = blog_post.get_meta_description()
        self.focus_keyword = blog_post.focus_keyword
        
    def analyze_content(self):
        """Comprehensive content analysis"""
        analysis = {
            'readability': self._analyze_readability(),
            'seo': self._analyze_seo(),
            'engagement': self._analyze_engagement(),
            'semantic': self._analyze_semantic(),
            'suggestions': self._generate_suggestions(),
            'score': 0
        }
        
        # Calculate overall score
        analysis['score'] = self._calculate_overall_score(analysis)
        return analysis
    
    def _analyze_readability(self):
        """Analyze content readability"""
        sentences = nltk.sent_tokenize(self.content)
        words = nltk.word_tokenize(self.content)
        
        return {
            'flesch_score': flesch_reading_ease(self.content),
            'grade_level': flesch_kincaid_grade(self.content),
            'avg_sentence_length': len(words) / len(sentences) if sentences else 0,
            'word_count': len(words),
            'sentence_count': len(sentences),
            'readability_grade': self._get_readability_grade(flesch_reading_ease(self.content))
        }
    
    def _analyze_seo(self):
        """Advanced SEO analysis"""
        content_lower = self.content.lower()
        title_lower = self.title.lower()
        
        # Keyword density analysis
        keyword_density = 0
        if self.focus_keyword:
            keyword_count = content_lower.count(self.focus_keyword.lower())
            keyword_density = (keyword_count / len(self.content.split())) * 100
        
        # Title optimization
        title_length = len(self.title)
        title_has_keyword = self.focus_keyword.lower() in title_lower if self.focus_keyword else False
        
        # Meta description analysis
        meta_length = len(self.meta_description)
        meta_has_keyword = self.focus_keyword.lower() in self.meta_description.lower() if self.focus_keyword else False
        
        # Header analysis
        headers = self._extract_headers()
        
        return {
            'keyword_density': round(keyword_density, 2),
            'title_optimization': {
                'length': title_length,
                'optimal_length': 30 <= title_length <= 60,
                'has_keyword': title_has_keyword
            },
            'meta_description': {
                'length': meta_length,
                'optimal_length': 120 <= meta_length <= 160,
                'has_keyword': meta_has_keyword
            },
            'headers': headers,
            'internal_links': self._count_internal_links(),
            'external_links': self._count_external_links(),
            'keyword_in_first_paragraph': self._keyword_in_first_paragraph()
        }
    
    def _analyze_engagement(self):
        """Analyze content for engagement factors"""
        sentences = nltk.sent_tokenize(self.content)
        
        # Question count
        questions = len([s for s in sentences if s.strip().endswith('?')])
        
        # Emotional words
        emotional_words = self._count_emotional_words()
        
        # Paragraph analysis
        paragraphs = [p.strip() for p in self.content.split('\n\n') if p.strip()]
        
        return {
            'question_count': questions,
            'emotional_word_count': emotional_words,
            'paragraph_count': len(paragraphs),
            'avg_paragraph_length': sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0,
            'call_to_action': self._detect_call_to_action(),
            'personal_pronouns': self._count_personal_pronouns()
        }
    
    def _analyze_semantic(self):
        """Semantic and topic analysis"""
        # Extract key phrases
        key_phrases = self._extract_key_phrases()
        
        # Topic modeling (simplified)
        topics = self._identify_topics()
        
        # Semantic density
        unique_words = len(set(self.content.lower().split()))
        total_words = len(self.content.split())
        semantic_density = unique_words / total_words if total_words > 0 else 0
        
        return {
            'key_phrases': key_phrases,
            'topics': topics,
            'semantic_density': round(semantic_density, 3),
            'content_depth_score': self._calculate_content_depth()
        }
    
    def _generate_suggestions(self):
        """Generate AI-powered improvement suggestions"""
        suggestions = []
        
        # Readability suggestions
        flesch_score = flesch_reading_ease(self.content)
        if flesch_score < 30:
            suggestions.append({
                'type': 'readability',
                'priority': 'high',
                'message': 'Content is very difficult to read. Consider shorter sentences and simpler words.',
                'action': 'Simplify sentence structure and use common vocabulary'
            })
        elif flesch_score < 60:
            suggestions.append({
                'type': 'readability',
                'priority': 'medium',
                'message': 'Content readability can be improved.',
                'action': 'Break up long sentences and use transition words'
            })
        
        # SEO suggestions
        if self.focus_keyword:
            keyword_density = (self.content.lower().count(self.focus_keyword.lower()) / len(self.content.split())) * 100
            if keyword_density < 0.5:
                suggestions.append({
                    'type': 'seo',
                    'priority': 'high',
                    'message': f'Keyword "{self.focus_keyword}" density is too low ({keyword_density:.1f}%).',
                    'action': 'Include the focus keyword naturally 2-3 more times'
                })
            elif keyword_density > 3:
                suggestions.append({
                    'type': 'seo',
                    'priority': 'medium',
                    'message': f'Keyword "{self.focus_keyword}" density is too high ({keyword_density:.1f}%).',
                    'action': 'Reduce keyword usage and use synonyms instead'
                })
        
        # Title suggestions
        if len(self.title) < 30:
            suggestions.append({
                'type': 'seo',
                'priority': 'medium',
                'message': 'Title is too short for optimal SEO.',
                'action': 'Expand title to 30-60 characters'
            })
        elif len(self.title) > 60:
            suggestions.append({
                'type': 'seo',
                'priority': 'high',
                'message': 'Title is too long and may be truncated in search results.',
                'action': 'Shorten title to under 60 characters'
            })
        
        # Content length suggestions
        word_count = len(self.content.split())
        if word_count < 300:
            suggestions.append({
                'type': 'content',
                'priority': 'high',
                'message': f'Content is too short ({word_count} words).',
                'action': 'Expand content to at least 300 words for better SEO'
            })
        
        return suggestions
    
    def _calculate_overall_score(self, analysis):
        """Calculate overall content intelligence score (0-100)"""
        score = 0
        
        # Readability score (25 points)
        flesch_score = analysis['readability']['flesch_score']
        if 60 <= flesch_score <= 80:
            score += 25
        elif 50 <= flesch_score < 90:
            score += 20
        elif flesch_score >= 30:
            score += 15
        else:
            score += 5
        
        # SEO score (50 points)
        seo = analysis['seo']
        
        # Title optimization (15 points)
        if seo['title_optimization']['optimal_length']:
            score += 10
        if seo['title_optimization']['has_keyword']:
            score += 5
        
        # Meta description (10 points)
        if seo['meta_description']['optimal_length']:
            score += 5
        if seo['meta_description']['has_keyword']:
            score += 5
        
        # Keyword density (10 points)
        if 0.5 <= seo['keyword_density'] <= 2.5:
            score += 10
        elif 0.1 <= seo['keyword_density'] <= 3.0:
            score += 5
        
        # Content length (15 points)
        word_count = analysis['readability']['word_count']
        if word_count >= 1000:
            score += 15
        elif word_count >= 500:
            score += 10
        elif word_count >= 300:
            score += 5
        
        # Engagement score (25 points)
        engagement = analysis['engagement']
        if engagement['question_count'] > 0:
            score += 5
        if engagement['call_to_action']:
            score += 5
        if engagement['paragraph_count'] >= 3:
            score += 5
        if 50 <= engagement['avg_paragraph_length'] <= 150:
            score += 10
        
        return min(score, 100)
    
    def _get_readability_grade(self, flesch_score):
        """Convert Flesch score to grade"""
        if flesch_score >= 90:
            return "Very Easy"
        elif flesch_score >= 80:
            return "Easy"
        elif flesch_score >= 70:
            return "Fairly Easy"
        elif flesch_score >= 60:
            return "Standard"
        elif flesch_score >= 50:
            return "Fairly Difficult"
        elif flesch_score >= 30:
            return "Difficult"
        else:
            return "Very Difficult"
    
    def _extract_headers(self):
        """Extract header information from content"""
        headers = {
            'h1': len(re.findall(r'<h1[^>]*>(.*?)</h1>', self.post.blog_body, re.IGNORECASE)),
            'h2': len(re.findall(r'<h2[^>]*>(.*?)</h2>', self.post.blog_body, re.IGNORECASE)),
            'h3': len(re.findall(r'<h3[^>]*>(.*?)</h3>', self.post.blog_body, re.IGNORECASE)),
            'total': 0
        }
        headers['total'] = headers['h1'] + headers['h2'] + headers['h3']
        return headers
    
    def _count_internal_links(self):
        """Count internal links in content"""
        # This is a simplified version - you'd want to make this more sophisticated
        return len(re.findall(r'<a[^>]*href="(?!http)[^"]*"[^>]*>', self.post.blog_body))
    
    def _count_external_links(self):
        """Count external links in content"""
        return len(re.findall(r'<a[^>]*href="https?://[^"]*"[^>]*>', self.post.blog_body))
    
    def _keyword_in_first_paragraph(self):
        """Check if focus keyword is in first paragraph"""
        if not self.focus_keyword:
            return False
        
        paragraphs = self.content.split('\n\n')
        if paragraphs:
            return self.focus_keyword.lower() in paragraphs[0].lower()
        return False
    
    def _count_emotional_words(self):
        """Count emotional words in content"""
        emotional_words = [
            'amazing', 'incredible', 'fantastic', 'wonderful', 'excellent',
            'outstanding', 'remarkable', 'extraordinary', 'brilliant', 'awesome',
            'shocking', 'surprising', 'unbelievable', 'devastating', 'heartbreaking',
            'inspiring', 'motivating', 'empowering', 'uplifting', 'encouraging'
        ]
        content_words = self.content.lower().split()
        return sum(1 for word in content_words if word in emotional_words)
    
    def _detect_call_to_action(self):
        """Detect call-to-action phrases"""
        cta_phrases = [
            'click here', 'learn more', 'read more', 'get started', 'sign up',
            'subscribe', 'download', 'contact us', 'buy now', 'order now',
            'try now', 'start today', 'join now', 'register now'
        ]
        content_lower = self.content.lower()
        return any(phrase in content_lower for phrase in cta_phrases)
    
    def _count_personal_pronouns(self):
        """Count personal pronouns for engagement"""
        pronouns = ['you', 'your', 'we', 'our', 'us', 'i', 'my', 'me']
        content_words = self.content.lower().split()
        return sum(1 for word in content_words if word in pronouns)
    
    def _extract_key_phrases(self):
        """Extract key phrases using TF-IDF"""
        try:
            # Simple key phrase extraction
            words = nltk.word_tokenize(self.content.lower())
            words = [word for word in words if word.isalpha() and len(word) > 3]
            
            # Get most common words
            word_freq = Counter(words)
            return [word for word, count in word_freq.most_common(10)]
        except:
            return []
    
    def _identify_topics(self):
        """Simplified topic identification"""
        # This is a basic implementation - you might want to use more sophisticated NLP
        sentences = nltk.sent_tokenize(self.content)
        if len(sentences) < 3:
            return []
        
        try:
            vectorizer = TfidfVectorizer(max_features=10, stop_words='english')
            tfidf_matrix = vectorizer.fit_transform(sentences)
            
            # Simple clustering
            n_clusters = min(3, len(sentences))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            kmeans.fit(tfidf_matrix)
            
            feature_names = vectorizer.get_feature_names_out()
            topics = []
            
            for i in range(n_clusters):
                cluster_center = kmeans.cluster_centers_[i]
                top_indices = cluster_center.argsort()[-3:][::-1]
                topic_words = [feature_names[idx] for idx in top_indices]
                topics.append(' '.join(topic_words))
            
            return topics
        except:
            return []
    
    def _calculate_content_depth(self):
        """Calculate content depth score"""
        # Factors: word count, unique words, sentence variety, paragraph structure
        words = self.content.split()
        unique_words = set(words)
        sentences = nltk.sent_tokenize(self.content)
        
        # Sentence length variety
        sentence_lengths = [len(s.split()) for s in sentences]
        length_variety = np.std(sentence_lengths) if len(sentence_lengths) > 1 else 0
        
        # Combine factors
        depth_score = (
            min(len(words) / 1000, 1) * 40 +  # Word count factor
            min(len(unique_words) / len(words), 0.8) * 30 +  # Vocabulary diversity
            min(length_variety / 10, 1) * 20 +  # Sentence variety
            min(len(sentences) / 20, 1) * 10  # Sentence count
        )
        
        return round(depth_score, 1)


# blogs/management/commands/analyze_content.py
