import json
import re
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class ReviewerPersona(Enum):
    SENIOR_DEVELOPER = "senior_developer"
    TECH_LEAD = "tech_lead"
    PAIR_PROGRAMMING = "pair_programming"
    MENTOR = "mentor"


@dataclass
class CodeQualityScore:
    overall_score: float  # 0-10 scale
    readability: float    # 0-10 scale
    performance: float    # 0-10 scale
    maintainability: float  # 0-10 scale
    best_practices: float  # 0-10 scale
    improvement_potential: float  # 0-10 scale
    
    def to_dict(self) -> Dict:
        return {
            "overall_score": round(self.overall_score, 1),
            "readability": round(self.readability, 1),
            "performance": round(self.performance, 1),
            "maintainability": round(self.maintainability, 1),
            "best_practices": round(self.best_practices, 1),
            "improvement_potential": round(self.improvement_potential, 1)
        }


class EmpathticCodeReviewer:
    def __init__(self, api_key: str, persona: ReviewerPersona = ReviewerPersona.SENIOR_DEVELOPER):
        self.client = OpenAI(api_key=api_key)
        self.persona = persona
        self.language_configs = self._init_language_configs()
        
    def _init_language_configs(self) -> Dict:
        """Initialize language-specific configurations and resources"""
        return {
            "python": {
                "extensions": [".py"],
                "keywords": ["def", "class", "import", "from", "if", "for", "while", "try", "except"],
                "resources": {
                    "naming": "[PEP 8 - Naming Conventions](https://peps.python.org/pep-0008/#naming-conventions)",
                    "performance": "[Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)",
                    "comprehension": "[List Comprehensions](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)",
                    "style": "[PEP 8 - Style Guide](https://peps.python.org/pep-0008/)",
                    "docstrings": "[PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)"
                }
            },
            "javascript": {
                "extensions": [".js", ".jsx", ".ts", ".tsx"],
                "keywords": ["function", "const", "let", "var", "class", "import", "export", "if", "for", "while"],
                "resources": {
                    "naming": "[JavaScript Naming Conventions](https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Writing_style_guide/Code_style_guide/JavaScript#naming_conventions)",
                    "performance": "[JavaScript Performance Best Practices](https://developer.mozilla.org/en-US/docs/Learn/Performance/JavaScript)",
                    "style": "[Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)",
                    "async": "[Async/Await Best Practices](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous/Async_await)",
                    "es6": "[ES6 Features Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/New_in_JavaScript/ECMAScript_6_support_in_Mozilla)"
                }
            },
            "java": {
                "extensions": [".java"],
                "keywords": ["public", "private", "protected", "class", "interface", "extends", "implements"],
                "resources": {
                    "naming": "[Java Naming Conventions](https://www.oracle.com/java/technologies/javase/codeconventions-namingconventions.html)",
                    "performance": "[Java Performance Tuning](https://docs.oracle.com/javase/8/docs/technotes/guides/performance/)",
                    "style": "[Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)",
                    "concurrency": "[Java Concurrency Tutorial](https://docs.oracle.com/javase/tutorial/essential/concurrency/)"
                }
            },
            "cpp": {
                "extensions": [".cpp", ".cc", ".cxx", ".h", ".hpp"],
                "keywords": ["class", "struct", "namespace", "template", "public", "private", "protected"],
                "resources": {
                    "naming": "[C++ Core Guidelines - Naming](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-naming)",
                    "performance": "[C++ Performance Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-performance)",
                    "style": "[Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)",
                    "modern": "[Modern C++ Best Practices](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)"
                }
            },
            "go": {
                "extensions": [".go"],
                "keywords": ["func", "type", "struct", "interface", "package", "import", "var", "const"],
                "resources": {
                    "naming": "[Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)",
                    "performance": "[Go Performance Tips](https://github.com/golang/go/wiki/Performance)",
                    "style": "[Effective Go](https://golang.org/doc/effective_go.html)",
                    "fmt": "[Go Formatting Guidelines](https://golang.org/doc/effective_go.html#formatting)"
                }
            }
        }
        
    def _detect_language(self, code_snippet: str) -> str:
        """Detect programming language from code snippet"""
        code_lower = code_snippet.lower().strip()
        
        # Language detection patterns
        if any(keyword in code_lower for keyword in ["def ", "class ", "import ", "from ", "elif", "__init__"]):
            return "python"
        elif any(keyword in code_lower for keyword in ["function", "const ", "let ", "=>", "console.log"]):
            return "javascript"
        elif any(keyword in code_lower for keyword in ["public class", "private ", "protected ", "import java"]):
            return "java"
        elif any(keyword in code_lower for keyword in ["#include", "namespace", "std::", "template<"]):
            return "cpp"
        elif any(keyword in code_lower for keyword in ["func ", "package ", "import (", "type "]):
            return "go"
        else:
            # Default to python for unknown languages
            return "python"
    
    def _assess_comment_severity(self, comment: str) -> str:
        """Assess the severity/harshness of a review comment"""
        harsh_indicators = [
            'bad', 'terrible', 'awful', 'stupid', 'dumb', 'wrong', 'never',
            'always', 'completely', 'totally', 'absolutely', 'obviously'
        ]
        
        neutral_indicators = [
            'could', 'might', 'consider', 'suggest', 'perhaps', 'maybe',
            'improvement', 'better', 'optimize'
        ]
        
        comment_lower = comment.lower()
        
        harsh_count = sum(1 for indicator in harsh_indicators if indicator in comment_lower)
        neutral_count = sum(1 for indicator in neutral_indicators if indicator in comment_lower)
        
        if harsh_count > neutral_count:
            return "harsh"
        elif neutral_count > harsh_count:
            return "neutral"
        else:
            return "moderate"
    
    def _get_relevant_resources(self, comment: str, code_snippet: str, language: str = None) -> List[str]:
        """Generate relevant documentation links based on comment content and language"""
        if language is None:
            language = self._detect_language(code_snippet)
            
        resources = []
        comment_lower = comment.lower()
        code_lower = code_snippet.lower()
        
        lang_config = self.language_configs.get(language, self.language_configs["python"])
        lang_resources = lang_config["resources"]
        
        # Generic patterns that apply to most languages
        if 'variable' in comment_lower or 'naming' in comment_lower:
            resources.append(lang_resources.get("naming", ""))
        
        if 'efficient' in comment_lower or 'performance' in comment_lower or 'loop' in comment_lower:
            resources.append(lang_resources.get("performance", ""))
            
        if 'style' in comment_lower or 'formatting' in comment_lower:
            resources.append(lang_resources.get("style", ""))
        
        # Language-specific patterns
        if language == "python":
            if 'comprehension' in comment_lower or 'list comprehension' in comment_lower:
                resources.append(lang_resources.get("comprehension", ""))
            if '== true' in code_lower or '== false' in code_lower:
                resources.append(lang_resources.get("style", ""))
            if 'function' in comment_lower or 'docstring' in comment_lower:
                resources.append(lang_resources.get("docstrings", ""))
                
        elif language == "javascript":
            if 'async' in comment_lower or 'promise' in comment_lower:
                resources.append(lang_resources.get("async", ""))
            if 'es6' in comment_lower or 'arrow' in comment_lower or 'const' in comment_lower:
                resources.append(lang_resources.get("es6", ""))
                
        elif language == "java":
            if 'thread' in comment_lower or 'concurrent' in comment_lower:
                resources.append(lang_resources.get("concurrency", ""))
                
        elif language == "cpp":
            if 'modern' in comment_lower or 'c++11' in comment_lower or 'c++14' in comment_lower:
                resources.append(lang_resources.get("modern", ""))
                
        elif language == "go":
            if 'format' in comment_lower or 'gofmt' in comment_lower:
                resources.append(lang_resources.get("fmt", ""))
        
        # Filter out empty resources
        return [r for r in resources if r]

    def _get_persona_prompt(self) -> str:
        """Get personality-specific prompt based on selected persona"""
        persona_prompts = {
            ReviewerPersona.SENIOR_DEVELOPER: """
            You are a seasoned senior software engineer with 10+ years of experience. You've seen it all and have a wealth of practical knowledge to share. Your approach is:
            - Pragmatic and solution-focused
            - Share real-world experiences and war stories when relevant
            - Balance perfectionism with practicality
            - Emphasize maintainability and long-term code health
            - Use phrases like "In my experience", "I've found that", "Consider the trade-offs"
            """,
            
            ReviewerPersona.TECH_LEAD: """
            You are a technical lead who balances technical excellence with team dynamics and project constraints. Your approach is:
            - Think about team consistency and standards
            - Consider project deadlines and business requirements
            - Focus on knowledge sharing and team growth
            - Explain the bigger picture and architectural implications
            - Use phrases like "For our team's consistency", "This aligns with our architecture", "Let's ensure everyone understands"
            """,
            
            ReviewerPersona.PAIR_PROGRAMMING: """
            You are a collaborative pair programming partner working side-by-side with the developer. Your approach is:
            - Very conversational and collaborative tone
            - Think out loud and invite discussion
            - Suggest exploring alternatives together
            - Ask thought-provoking questions
            - Use phrases like "What do you think about", "Let's try", "How about we explore", "I'm curious about"
            """,
            
            ReviewerPersona.MENTOR: """
            You are a patient, encouraging mentor focused on teaching and growth. Your approach is:
            - Extremely encouraging and positive
            - Break down complex concepts into digestible pieces
            - Celebrate small wins and progress
            - Provide learning resources and next steps
            - Use phrases like "Great job on", "This is a learning opportunity", "Let's build on this", "You're on the right track"
            """
        }
        
        return persona_prompts.get(self.persona, persona_prompts[ReviewerPersona.SENIOR_DEVELOPER])
    
    def _create_system_prompt(self, severity: str, language: str = "python") -> str:
        """Create a system prompt tailored to the comment severity and language"""
        persona_context = self._get_persona_prompt()
        
        base_prompt = f"""You are an empathetic and educational code reviewer. Your goal is to transform critical feedback into constructive, encouraging guidance that helps developers learn and grow.
        
        {persona_context}
        
        Code Language Context: You are reviewing {language.upper()} code. Use language-specific terminology, conventions, and best practices in your explanations.

        Key principles:
        1. Always start with something positive or encouraging
        2. Explain the 'why' behind suggestions with clear technical reasoning
        3. Provide concrete, improved code examples in the correct language syntax
        4. Use inclusive language that builds confidence
        5. Focus on learning opportunities rather than mistakes
        6. Reference language-specific style guides and best practices when relevant"""

        severity_adjustments = {
            "harsh": " Pay special attention to softening harsh language and being extra encouraging. The original feedback may have been blunt or discouraging, so focus on building the developer's confidence while still conveying the technical improvement needed.",
            "moderate": " Maintain a balanced, professional tone while being supportive and educational.",
            "neutral": " The original feedback was already fairly neutral, so focus on making it more educational and adding the 'why' behind suggestions."
        }
        
        return base_prompt + severity_adjustments.get(severity, "")

    def _calculate_code_quality_score(self, code_snippet: str, comments: List[str], language: str) -> CodeQualityScore:
        """Calculate code quality score based on code and review comments"""
        # Basic scoring algorithm - can be enhanced with more sophisticated analysis
        total_comments = len(comments)
        
        # Start with baseline scores
        readability = 7.0
        performance = 7.0  
        maintainability = 7.0
        best_practices = 7.0
        
        # Deduct points based on comment types
        severity_weights = {"harsh": -2.0, "moderate": -1.0, "neutral": -0.5}
        
        for comment in comments:
            severity = self._assess_comment_severity(comment)
            weight = severity_weights.get(severity, -0.5)
            
            comment_lower = comment.lower()
            
            # Specific issue type penalties
            if any(word in comment_lower for word in ["naming", "variable", "unclear"]):
                readability += weight
            if any(word in comment_lower for word in ["efficient", "performance", "slow", "optimize"]):
                performance += weight
            if any(word in comment_lower for word in ["maintainability", "complex", "structure"]):
                maintainability += weight
            if any(word in comment_lower for word in ["convention", "style", "best practice", "standard"]):
                best_practices += weight
        
        # Clamp scores to 0-10 range
        readability = max(0, min(10, readability))
        performance = max(0, min(10, performance))
        maintainability = max(0, min(10, maintainability))
        best_practices = max(0, min(10, best_practices))
        
        # Calculate overall score
        overall_score = (readability + performance + maintainability + best_practices) / 4
        
        # Calculate improvement potential (inverse of current score)
        improvement_potential = 10 - overall_score
        
        return CodeQualityScore(
            overall_score=overall_score,
            readability=readability,
            performance=performance,
            maintainability=maintainability,
            best_practices=best_practices,
            improvement_potential=improvement_potential
        )
    
    def _generate_empathetic_review(self, code_snippet: str, comments: List[str], language: str = None) -> str:
        """Generate empathetic review using OpenAI with sophisticated prompting"""
        
        if language is None:
            language = self._detect_language(code_snippet)
            
        # Assess overall severity
        severities = [self._assess_comment_severity(comment) for comment in comments]
        overall_severity = max(severities, key=severities.count)
        
        system_prompt = self._create_system_prompt(overall_severity, language)
        
        user_prompt = f"""Please transform the following {language.upper()} code review comments into empathetic, educational feedback. For each comment, provide:

1. **Positive Rephrasing**: A gentle, encouraging version that maintains the technical point
2. **The 'Why'**: Clear explanation of the underlying software principle (performance, readability, maintainability, etc.)
3. **Suggested Improvement**: Concrete code example demonstrating the fix

Code Snippet:
```{language}
{code_snippet}
```

Original Comments:
{json.dumps(comments, indent=2)}

Format your response as markdown with a section for each comment using this structure:

---
### Analysis of Comment: "[original comment]"

**Positive Rephrasing:** [encouraging version]

**The 'Why':** [technical explanation]

**Suggested Improvement:**
```{language}
[improved code]
```

[If applicable, add relevant resources or additional context]

---

After addressing all comments, add a "Summary" section with an encouraging overall assessment of the code and the developer's progress."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise Exception(f"Error generating review: {str(e)}")

    def _enhance_with_resources(self, review_content: str, code_snippet: str, comments: List[str], language: str = None) -> str:
        """Enhance the review with relevant resource links"""
        
        if language is None:
            language = self._detect_language(code_snippet)
            
        all_resources = []
        for comment in comments:
            resources = self._get_relevant_resources(comment, code_snippet, language)
            all_resources.extend(resources)
        
        # Remove duplicates while preserving order
        unique_resources = list(dict.fromkeys(all_resources))
        
        if unique_resources:
            resource_section = "\n\n## Additional Resources\n\nFor further learning, consider reviewing these resources:\n\n"
            for resource in unique_resources:
                resource_section += f"- {resource}\n"
            
            review_content += resource_section
        
        return review_content

    def generate_review_report(self, input_data: Dict) -> Tuple[str, CodeQualityScore]:
        """Generate a complete empathetic review report with quality scoring"""
        
        try:
            # Validate input
            if "code_snippet" not in input_data or "review_comments" not in input_data:
                raise ValueError("Input must contain 'code_snippet' and 'review_comments' keys")
            
            code_snippet = input_data["code_snippet"]
            comments = input_data["review_comments"]
            
            if not isinstance(comments, list) or not comments:
                raise ValueError("'review_comments' must be a non-empty list")
            
            # Detect language
            language = self._detect_language(code_snippet)
            
            # Calculate quality score
            quality_score = self._calculate_code_quality_score(code_snippet, comments, language)
            
            # Generate empathetic review
            review_content = self._generate_empathetic_review(code_snippet, comments, language)
            
            # Enhance with resources
            enhanced_review = self._enhance_with_resources(review_content, code_snippet, comments, language)
            
            # Add header with language and persona info
            persona_name = self.persona.value.replace('_', ' ').title()
            header = f"# 📝 Empathetic Code Review Report\n\n**Language:** {language.title()} | **Reviewer Persona:** {persona_name} | **Overall Quality Score:** {quality_score.overall_score}/10\n\n"
            
            final_report = header + enhanced_review
            
            return final_report, quality_score
            
        except Exception as e:
            raise Exception(f"Failed to generate review report: {str(e)}")
    
    def set_persona(self, persona: ReviewerPersona):
        """Change the reviewer persona"""
        self.persona = persona
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages"""
        return list(self.language_configs.keys())
    
    def analyze_code_quality(self, code_snippet: str, comments: List[str]) -> Dict:
        """Standalone method to analyze code quality without full review"""
        language = self._detect_language(code_snippet)
        quality_score = self._calculate_code_quality_score(code_snippet, comments, language)
        
        return {
            "language": language,
            "quality_metrics": quality_score.to_dict(),
            "total_issues": len(comments),
            "severity_breakdown": {
                severity: sum(1 for c in comments if self._assess_comment_severity(c) == severity)
                for severity in ["harsh", "moderate", "neutral"]
            }
        }


def parse_json_input(json_string: str) -> Dict:
    """Parse and validate JSON input"""
    try:
        data = json.loads(json_string)
        return data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")