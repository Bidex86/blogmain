# blogs/voice_search.py
import re
import json
from collections import Counter
from django.utils.html import strip_tags
from django.template.loader import render_to_string

class VoiceSearchOptimizer:
    """Voice search optimization and featured snippet preparation"""
    
    def __init__(self, blog_post):
        self.post = blog_post
        self.content = strip_tags(blog_post.blog_body)
        self.title = blog_post.title
        
    def analyze_voice_readiness(self):
        """Comprehensive voice search readiness analysis"""
        analysis = {
            'featured_snippet_potential': self._analyze_featured_snippet_potential(),
            'question_answer_pairs': self._extract_question_answers(),
            'conversational_score': self._calculate_conversational_score(),
            'schema_markup': self._generate_schema_markup(),
            'voice_keywords': self._identify_voice_keywords(),
            'readability_for_voice': self._analyze_voice_readability(),
            'overall_voice_score': 0
        }
        
        analysis['overall_voice_score'] = self._calculate_voice_score(analysis)
        return analysis
    
    def _analyze_featured_snippet_potential(self):
        """Analyze potential for featured snippets"""
        snippets = {
            'paragraph': self._find_definition_paragraphs(),
            'list': self._find_list_content(),
            'table': self._find_table_content(),
            'how_to': self._find_how_to_content(),
        }
        
        # Score each type
        for snippet_type, content in snippets.items():
            if content:
                snippets[snippet_type] = {
                    'content': content,
                    'score': self._score_snippet_content(content, snippet_type),
                    'optimized': self._is_snippet_optimized(content, snippet_type)
                }
            else:
                snippets[snippet_type] = {'content': None, 'score': 0, 'optimized': False}
        
        return snippets
    
    def _extract_question_answers(self):
        """Extract question-answer pairs for voice search"""
        qa_pairs = []
        
        # Find FAQ-style content
        faq_pattern = r'(?:^|\n)(?:Q:|Question:|Query:|\d+\.)\s*([^?\n]*\?)\s*(?:\n|$)(?:A:|Answer:|Response:)?\s*([^\n]+(?:\n[^\n]+)*?)(?=\n(?:Q:|Question:|Query:|\d+\.)|$)'
        faq_matches = re.findall(faq_pattern, self.content, re.MULTILINE | re.IGNORECASE)
        
        for question, answer in faq_matches:
            qa_pairs.append({
                'question': question.strip(),
                'answer': answer.strip()[:200] + '...' if len(answer.strip()) > 200 else answer.strip(),
                'type': 'faq'
            })
        
        # Find implied questions from headers
        headers = self._extract_content_headers()
        for header in headers:
            if any(word in header.lower() for word in ['what', 'how', 'why', 'when', 'where', 'who']):
                # Try to find the content following this header
                header_content = self._get_content_after_header(header)
                if header_content:
                    qa_pairs.append({
                        'question': header if header.endswith('?') else f"{header}?",
                        'answer': header_content[:200] + '...' if len(header_content) > 200 else header_content,
                        'type': 'header_based'
                    })
        
        return qa_pairs
    
    def _calculate_conversational_score(self):
        """Calculate how conversational the content is"""
        score_factors = {
            'personal_pronouns': 0,
            'question_words': 0,
            'conversational_phrases': 0,
            'sentence_starters': 0,
            'readability': 0
        }
        
        # Personal pronouns (you, we, I, etc.)
        personal_pronouns = ['you', 'your', 'we', 'our', 'us', 'i', 'my', 'me']
        content_words = self.content.lower().split()
        pronoun_count = sum(1 for word in content_words if word in personal_pronouns)
        score_factors['personal_pronouns'] = min(pronoun_count / len(content_words) * 100, 10)
        
        # Question words
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        question_count = sum(1 for word in content_words if word in question_words)
        score_factors['question_words'] = min(question_count / len(content_words) * 200, 15)
        
        # Conversational phrases
        conversational_phrases = [
            'let me', 'you should', 'here\'s how', 'the thing is', 'believe it or not',
            'to be honest', 'in my opinion', 'as you can see', 'simply put', 'in other words'
        ]
        content_lower = self.content.lower()
        phrase_count = sum(1 for phrase in conversational_phrases if phrase in content_lower)
        score_factors['conversational_phrases'] = min(phrase_count * 5, 20)
        
        # Sentence starters that sound natural
        natural_starters = [
            'now', 'so', 'well', 'also', 'plus', 'however', 'meanwhile', 'furthermore'
        ]
        sentences = self.content.split('.')
        starter_count = sum(1 for sentence in sentences 
                          if any(sentence.strip().lower().startswith(starter) 
                                for starter in natural_starters))
        score_factors['sentence_starters'] = min(starter_count / len(sentences) * 50, 15)
        
        # Readability for voice (simpler is better for voice)
        from textstat import flesch_reading_ease
        flesch_score = flesch_reading_ease(self.content)
        if flesch_score >= 80:
            score_factors['readability'] = 20
        elif flesch_score >= 70:
            score_factors['readability'] = 15
        elif flesch_score >= 60:
            score_factors['readability'] = 10
        else:
            score_factors['readability'] = 5
        
        total_score = sum(score_factors.values())
        return {
            'total_score': round(total_score, 1),
            'factors': score_factors,
            'grade': self._get_conversational_grade(total_score)
        }
    
    def _generate_schema_markup(self):
        """Generate schema markup for voice search"""
        schemas = {}
        
        # FAQ Schema
        qa_pairs = self._extract_question_answers()
        if qa_pairs:
            faq_schema = {
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": []
            }
            
            for qa in qa_pairs[:5]:  # Limit to top 5
                faq_schema["mainEntity"].append({
                    "@type": "Question",
                    "name": qa['question'],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": qa['answer']
                    }
                })
            
            schemas['faq'] = faq_schema
        
        # How-to Schema
        how_to_content = self._find_how_to_content()
        if how_to_content:
            howto_schema = {
                "@context": "https://schema.org",
                "@type": "HowTo",
                "name": self.post.title,
                "description": self.post.get_meta_description(),
                "totalTime": f"PT{self.post.get_reading_time()}M",
                "supply": [],
                "tool": [],
                "step": []
            }
            
            # Extract steps
            steps = self._extract_steps_from_content()
            for i, step in enumerate(steps, 1):
                howto_schema["step"].append({
                    "@type": "HowToStep",
                    "position": i,
                    "name": f"Step {i}",
                    "text": step
                })
            
            schemas['howto'] = howto_schema
        
        # Article Schema with speakable
        article_schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": self.post.title,
            "description": self.post.get_meta_description(),
            "author": {
                "@type": "Person",
                "name": self.post.author.get_full_name() or self.post.author.username
            },
            "datePublished": self.post.created_at.isoformat(),
            "dateModified": self.post.updated_at.isoformat(),
            "speakable": {
                "@type": "SpeakableSpecification",
                "cssSelector": [".post-title", ".post-summary", ".post-content p:first-of-type"]
            }
        }
        
        schemas['article'] = article_schema
        
        return schemas
    
    def _identify_voice_keywords(self):
        """Identify keywords that are likely to be used in voice search"""
        voice_patterns = [
            # Question patterns
            r'\b(?:what|how|why|when|where|who|which)\s+(?:is|are|do|does|can|will|would|should)\b.*?[.?!]',
            # Local search patterns
            r'\b(?:near me|nearby|close to|in my area|local)\b',
            # Action patterns
            r'\b(?:how to|ways to|steps to|guide to|tutorial)\b',
            # Comparison patterns
            r'\b(?:best|top|compare|vs|versus|better than|alternatives to)\b',
        ]
        
        voice_keywords = []
        content_lower = self.content.lower()
        
        for pattern in voice_patterns:
            matches = re.findall(pattern, content_lower, re.IGNORECASE)
            voice_keywords.extend(matches)
        
        # Extract long-tail keywords (3+ words)
        words = content_lower.split()
        long_tail_phrases = []
        for i in range(len(words) - 2):
            phrase = ' '.join(words[i:i+3])
            if len(phrase) > 10 and phrase.count(' ') >= 2:
                long_tail_phrases.append(phrase)
        
        # Get most common long-tail phrases
        phrase_counter = Counter(long_tail_phrases)
        common_phrases = [phrase for phrase, count in phrase_counter.most_common(10) if count > 1]
        
        return {
            'voice_patterns': voice_keywords[:10],
            'long_tail_phrases': common_phrases,
            'local_intent': any('near me' in kw or 'nearby' in kw for kw in voice_keywords),
            'question_intent': any(kw.startswith(('what', 'how', 'why', 'when', 'where')) for kw in voice_keywords)
        }
    
    def _analyze_voice_readability(self):
        """Analyze readability specifically for voice search"""
        sentences = self.content.split('.')
        
        analysis = {
            'avg_sentence_length': 0,
            'complex_words': 0,
            'passive_voice_count': 0,
            'reading_level': '',
            'voice_friendly_score': 0
        }
        
        if sentences:
            # Average sentence length (shorter is better for voice)
            total_words = sum(len(sentence.split()) for sentence in sentences if sentence.strip())
            analysis['avg_sentence_length'] = total_words / len(sentences)
            
            # Complex words (3+ syllables)
            words = self.content.lower().split()
            complex_words = [word for word in words if self._count_syllables(word) >= 3]
            analysis['complex_words'] = len(complex_words)
            
            # Passive voice detection (simplified)
            passive_indicators = ['was', 'were', 'been', 'being', 'is', 'are', 'am']
            past_participles = ['ed', 'en', 'ing']  # Simplified check
            
            passive_count = 0
            for sentence in sentences:
                sentence_words = sentence.lower().split()
                if any(indicator in sentence_words for indicator in passive_indicators):
                    if any(word.endswith(suffix) for word in sentence_words for suffix in past_participles):
                        passive_count += 1
            
            analysis['passive_voice_count'] = passive_count
            
            # Voice-friendly score
            score = 100
            
            # Penalize long sentences (>20 words)
            if analysis['avg_sentence_length'] > 20:
                score -= min((analysis['avg_sentence_length'] - 20) * 2, 30)
            
            # Penalize too many complex words
            complex_ratio = analysis['complex_words'] / len(words) if words else 0
            if complex_ratio > 0.15:  # >15% complex words
                score -= min((complex_ratio - 0.15) * 100, 25)
            
            # Penalize passive voice
            passive_ratio = passive_count / len(sentences) if sentences else 0
            if passive_ratio > 0.2:  # >20% passive sentences
                score -= min((passive_ratio - 0.2) * 50, 20)
            
            analysis['voice_friendly_score'] = max(score, 0)
        
        return analysis
    
    def _calculate_voice_score(self, analysis):
        """Calculate overall voice search optimization score"""
        score = 0
        
        # Featured snippet potential (30 points)
        snippet_scores = [data['score'] for data in analysis['featured_snippet_potential'].values() if isinstance(data, dict)]
        if snippet_scores:
            score += min(max(snippet_scores) * 3, 30)
        
        # Question-answer pairs (25 points)
        qa_count = len(analysis['question_answer_pairs'])
        score += min(qa_count * 5, 25)
        
        # Conversational score (25 points)
        conversational_score = analysis['conversational_score']['total_score']
        score += min(conversational_score * 0.3, 25)
        
        # Voice keywords (10 points)
        voice_kw = analysis['voice_keywords']
        if voice_kw['voice_patterns'] or voice_kw['long_tail_phrases']:
            score += 5
        if voice_kw['question_intent']:
            score += 3
        if voice_kw['local_intent']:
            score += 2
        
        # Voice readability (10 points)
        readability_score = analysis['readability_for_voice']['voice_friendly_score']
        score += min(readability_score * 0.1, 10)
        
        return min(round(score, 1), 100)
    
    # Helper methods
    def _find_definition_paragraphs(self):
        """Find paragraphs that define concepts"""
        definition_patterns = [
            r'(?:is|are|means|refers to|defined as|known as)\s+([^.!?]+[.!?])',
            r'(\w+)\s+(?:is|are)\s+(?:a|an|the)?\s*([^.!?]+[.!?])'
        ]
        
        definitions = []
        for pattern in definition_patterns:
            matches = re.findall(pattern, self.content, re.IGNORECASE)
            definitions.extend(matches)
        
        return definitions[:3]  # Return top 3
    
    def _find_list_content(self):
        """Find list-style content"""
        # Look for numbered lists or bullet points
        list_patterns = [
            r'(?:^|\n)(?:\d+\.|[-*•])\s+([^\n]+)',  # Numbered or bulleted lists
            r'(?:first|second|third|fourth|fifth|next|finally),?\s+([^.!?]+[.!?])',  # Sequential items
        ]
        
        lists = []
        for pattern in list_patterns:
            matches = re.findall(pattern, self.content, re.MULTILINE | re.IGNORECASE)
            if matches:
                lists.extend(matches[:5])  # Max 5 items
        
        return lists
    
    def _find_table_content(self):
        """Find tabular information that could be featured"""
        # This is simplified - you might want to parse actual HTML tables
        table_indicators = ['comparison', 'vs', 'versus', 'price', 'cost', 'features']
        
        if any(indicator in self.content.lower() for indicator in table_indicators):
            # Extract comparison-like content
            comparison_pattern = r'([A-Z][^.!?]*(?:vs|versus|compared to)[^.!?]*[.!?])'
            comparisons = re.findall(comparison_pattern, self.content)
            return comparisons[:3]
        
        return []
    
    def _find_how_to_content(self):
        """Find how-to style content"""
        how_to_patterns = [
            'how to',
            'steps to',
            'guide to',
            'tutorial',
            'instructions'
        ]
        
        content_lower = self.content.lower()
        return any(pattern in content_lower for pattern in how_to_patterns)
    
    def _score_snippet_content(self, content, snippet_type):
        """Score content for featured snippet potential"""
        if not content:
            return 0
        
        base_score = 5
        
        # Length optimization
        if snippet_type == 'paragraph':
            optimal_length = 40 <= len(str(content)) <= 60
            if optimal_length:
                base_score += 3
        elif snippet_type == 'list':
            if 3 <= len(content) <= 8:  # Optimal list length
                base_score += 3
        
        # Keyword presence
        if self.post.focus_keyword and self.post.focus_keyword.lower() in str(content).lower():
            base_score += 2
        
        return base_score
    
    def _is_snippet_optimized(self, content, snippet_type):
        """Check if content is optimized for snippets"""
        if not content:
            return False
        
        try:
            # Ensure all values are boolean
            has_keyword = False
            if hasattr(self.post, 'focus_keyword') and self.post.focus_keyword:
                has_keyword = self.post.focus_keyword.lower() in str(content).lower()
            
            appropriate_length = self._check_snippet_length(content, snippet_type)
            
            # Count boolean True values only
            score = sum([has_keyword, appropriate_length])
            return score >= 2
    
        except Exception:
            return False 
       
    def _check_snippet_length(self, content, snippet_type):
        """Check if content length is appropriate for snippet type"""
        content_str = str(content)
        
        if snippet_type == 'paragraph':
            return 40 <= len(content_str) <= 300
        elif snippet_type == 'list':
            return isinstance(content, list) and 3 <= len(content) <= 8
        elif snippet_type == 'table':
            return 50 <= len(content_str) <= 500
        
        return True
    
    def _extract_content_headers(self):
        """Extract headers from the content"""
        # This assumes headers are marked in the original content
        header_pattern = r'<h[1-6][^>]*>([^<]+)</h[1-6]>'
        headers = re.findall(header_pattern, self.post.blog_body, re.IGNORECASE)
        return [strip_tags(header).strip() for header in headers]
    
    def _get_content_after_header(self, header):
        """Get content that follows a specific header"""
        # Simplified implementation
        header_index = self.content.find(header)
        if header_index != -1:
            remaining_content = self.content[header_index + len(header):]
            # Get first paragraph after header
            first_paragraph = remaining_content.split('\n\n')[0]
            return first_paragraph.strip()
        return ""
    
    def _get_conversational_grade(self, score):
        """Convert conversational score to grade"""
        if score >= 70:
            return "Excellent"
        elif score >= 55:
            return "Good"
        elif score >= 40:
            return "Fair"
        elif score >= 25:
            return "Poor"
        else:
            return "Very Poor"
    
    def _extract_steps_from_content(self):
        """Extract step-by-step instructions"""
        step_patterns = [
            r'(?:step\s*\d+:?|first|second|third|fourth|fifth|next|finally)[:\s]*([^.!?]+[.!?])',
            r'(?:^|\n)\d+\.\s*([^\n]+)',
        ]
        
        steps = []
        for pattern in step_patterns:
            matches = re.findall(pattern, self.content, re.MULTILINE | re.IGNORECASE)
            steps.extend(matches)
        
        return steps[:10]  # Max 10 steps
    
    def _count_syllables(self, word):
        """Simple syllable counting"""
        word = word.lower()
        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False
        
        for char in word:
            if char in vowels:
                if not prev_was_vowel:
                    syllable_count += 1
                prev_was_vowel = True
            else:
                prev_was_vowel = False
        
        # Handle silent 'e'
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1
        
        return max(syllable_count, 1)


