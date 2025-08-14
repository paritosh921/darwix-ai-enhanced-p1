import streamlit as st
import json
import os
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from code_reviewer import EmpathticCodeReviewer, parse_json_input, ReviewerPersona, CodeQualityScore


def create_quality_chart(quality_score: CodeQualityScore) -> go.Figure:
    """Create a radar chart for code quality metrics"""
    categories = ['Readability', 'Performance', 'Maintainability', 'Best Practices']
    values = [quality_score.readability, quality_score.performance, 
              quality_score.maintainability, quality_score.best_practices]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Current Score',
        line_color='rgb(30, 144, 255)',
        fillcolor='rgba(30, 144, 255, 0.3)'
    ))
    
    # Add potential improvement line
    max_values = [10] * len(categories)
    fig.add_trace(go.Scatterpolar(
        r=max_values,
        theta=categories,
        fill='toself',
        name='Maximum Score',
        line_color='rgb(144, 238, 144)',
        fillcolor='rgba(144, 238, 144, 0.1)',
        opacity=0.5
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )
        ),
        showlegend=True,
        title="Code Quality Assessment",
        height=400
    )
    
    return fig


def create_score_gauge(overall_score: float) -> go.Figure:
    """Create a gauge chart for overall score"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=overall_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Overall Quality Score"},
        delta={'reference': 7.0, 'position': "top"},
        gauge={
            'axis': {'range': [None, 10]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 4], 'color': "lightgray"},
                {'range': [4, 7], 'color': "yellow"},
                {'range': [7, 10], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 9
            }
        }
    ))
    
    fig.update_layout(height=300)
    return fig


def load_example_data(language="python"):
    """Load example data for different languages"""
    examples = {
        "python": {
            "code_snippet": """def get_active_users(users):
    results = []
    for u in users:
        if u.is_active == True and u.profile_complete == True:
            results.append(u)
    return results""",
            "review_comments": [
                "This is inefficient. Don't loop twice conceptually.",
                "Variable 'u' is a bad name.",
                "Boolean comparison '== True' is redundant."
            ]
        },
        "javascript": {
            "code_snippet": """function getUserData(users) {
    var result = [];
    for (var i = 0; i < users.length; i++) {
        if (users[i].active == true && users[i].verified == true) {
            result.push(users[i]);
        }
    }
    return result;
}""",
            "review_comments": [
                "Use const/let instead of var for better scoping.",
                "This loop is inefficient, consider using filter().",
                "Boolean comparison with == true is redundant.",
                "Function name could be more descriptive."
            ]
        },
        "java": {
            "code_snippet": """public List<User> getActiveUsers(List<User> users) {
    List<User> result = new ArrayList<>();
    for (int i = 0; i < users.size(); i++) {
        User u = users.get(i);
        if (u.isActive() == true && u.isVerified() == true) {
            result.add(u);
        }
    }
    return result;
}""",
            "review_comments": [
                "Enhanced for-loop would be more readable.",
                "Boolean comparison with == true is unnecessary.",
                "Variable name 'u' is not descriptive.",
                "Consider using streams for functional approach."
            ]
        }
    }
    return examples.get(language, examples["python"])


def main():
    st.set_page_config(
        page_title="Empathetic Code Reviewer Pro",
        page_icon="📝",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .persona-info {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
    .quality-metrics {
        background: #fff3e0;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ff9800;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        border-radius: 8px 8px 0 0;
    }
    .success-message {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Enhanced Header
    st.markdown("""
    <div class="main-header">
        <h1>📝 Empathetic Code Reviewer Pro</h1>
        <p style="font-size: 1.2em; margin: 0.5rem 0;">Transform critical feedback into constructive growth opportunities</p>
        <p style="margin: 0;"><em>✨ Multi-language support • 🎭 AI Personas • 📊 Quality Analytics • 🔗 Smart Resources</em></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Enhanced Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # API Key input
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            help="Enter your OpenAI API key. It will be used securely and not stored."
        )
        
        st.markdown("---")
        
        # Persona Selection
        st.subheader("🎭 Reviewer Persona")
        persona_options = {
            "Senior Developer": ReviewerPersona.SENIOR_DEVELOPER,
            "Tech Lead": ReviewerPersona.TECH_LEAD,
            "Pair Programming Partner": ReviewerPersona.PAIR_PROGRAMMING,
            "Patient Mentor": ReviewerPersona.MENTOR
        }
        
        selected_persona = st.selectbox(
            "Choose reviewer style:",
            options=list(persona_options.keys()),
            help="Different personas will adjust the tone and approach of the review"
        )
        
        persona_descriptions = {
            "Senior Developer": "🎯 Pragmatic, experienced, shares real-world insights",
            "Tech Lead": "📋 Focuses on team standards and architectural implications", 
            "Pair Programming Partner": "💬 Collaborative, conversational, invites discussion",
            "Patient Mentor": "🌱 Encouraging, educational, celebrates progress"
        }
        
        st.markdown(f"""
        <div class="persona-info">
            {persona_descriptions[selected_persona]}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Language Detection Info
        st.subheader("🌐 Multi-Language Support")
        supported_langs = ["Python", "JavaScript", "Java", "C++", "Go"]
        for lang in supported_langs:
            st.write(f"✅ {lang}")
        st.info("💡 Language is auto-detected from your code")
        
        st.markdown("---")
        
        # Example data options
        st.subheader("📋 Load Examples")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🐍 Python", use_container_width=True):
                st.session_state['example_loaded'] = 'python'
            if st.button("☕ Java", use_container_width=True):
                st.session_state['example_loaded'] = 'java'
        with col2:
            if st.button("🟨 JavaScript", use_container_width=True):
                st.session_state['example_loaded'] = 'javascript'
            if st.button("⚡ More Soon", use_container_width=True, disabled=True):
                pass
        
        st.markdown("---")
        
        # Enhanced Instructions
        st.markdown("""
        ### 🚀 Key Features:
        **🔍 Smart Analysis**
        - Auto language detection
        - Context-aware feedback
        - Quality scoring metrics
        
        **🎯 Personalized Experience**  
        - Multiple reviewer personas
        - Severity-based tone adjustment
        - Learning-focused approach
        
        **📚 Educational Resources**
        - Language-specific documentation
        - Best practice guides
        - Performance optimization tips
        
        ### 📖 How to Use:
        1. Enter your OpenAI API key above
        2. Choose your preferred reviewer persona
        3. Load an example or paste your JSON
        4. Generate empathetic analysis!
        """)
    
    # Main content with tabs
    tab1, tab2, tab3 = st.tabs(["📝 Review Generator", "📊 Quality Analytics", "📚 Resources & Examples"])
    
    with tab1:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.header("📥 Input")
            
            # Load example if requested  
            example_type = st.session_state.get('example_loaded', False)
            if example_type:
                example_data = load_example_data(example_type)
                default_json = json.dumps(example_data, indent=2)
                st.session_state['example_loaded'] = False
                st.success(f"✅ Loaded {example_type.title()} example!")
            else:
                default_json = """{
  "code_snippet": "your code here",
  "review_comments": [
    "first critical comment",
    "second critical comment"
  ]
}"""
            
            # JSON input
            json_input = st.text_area(
                "JSON Input",
                value=default_json,
                height=400,
                help="Enter JSON with 'code_snippet' and 'review_comments' keys"
            )
            
            # Validate JSON in real-time
            try:
                if json_input.strip():
                    parsed_data = parse_json_input(json_input)
                    st.success("✅ Valid JSON format")
                    
                    # Show enhanced preview
                    with st.expander("🔍 Preview Parsed Data"):
                        # Auto-detect language for preview
                        if api_key:
                            temp_reviewer = EmpathticCodeReviewer(api_key)
                            detected_lang = temp_reviewer._detect_language(parsed_data.get('code_snippet', ''))
                            st.info(f"🌐 Detected Language: **{detected_lang.title()}**")
                        
                        st.code(parsed_data.get('code_snippet', ''), language=detected_lang if api_key else 'python')
                        
                        st.write("💬 **Review Comments:**")
                        for i, comment in enumerate(parsed_data.get('review_comments', []), 1):
                            severity = "🔴 Harsh" if any(word in comment.lower() for word in ['bad', 'terrible', 'wrong']) else "🟡 Moderate" if any(word in comment.lower() for word in ['inefficient', 'should']) else "🟢 Neutral"
                            st.write(f"{i}. {comment} {severity}")
                
            except ValueError as e:
                st.error(f"❌ JSON Error: {str(e)}")
                parsed_data = None
            
            # Generate button
            generate_button = st.button(
                "🚀 Generate Empathetic Review",
                use_container_width=True,
                type="primary",
                disabled=not (api_key and json_input.strip())
            )
        
        with col2:
            st.header("📤 Output")
            
            if generate_button:
                if not api_key:
                    st.error("❌ Please enter your OpenAI API key")
                    return
                
                try:
                    # Validate input
                    input_data = parse_json_input(json_input)
                    
                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("🔍 Analyzing code and comments...")
                    progress_bar.progress(25)
                    
                    # Initialize reviewer with persona
                    reviewer = EmpathticCodeReviewer(api_key, persona_options[selected_persona])
                    
                    status_text.text("🎭 Applying reviewer persona...")
                    progress_bar.progress(50)
                    
                    status_text.text("🤖 Generating empathetic feedback...")
                    progress_bar.progress(75)
                    
                    # Generate review
                    review_report, quality_score = reviewer.generate_review_report(input_data)
                    
                    status_text.text("✨ Finalizing report...")
                    progress_bar.progress(100)
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display success message
                    st.markdown("""
                    <div class="success-message">
                        ✅ <strong>Review generated successfully!</strong><br>
                        🎯 Persona applied • 📊 Quality scored • 🔗 Resources linked
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Quality metrics summary
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.metric("Overall Score", f"{quality_score.overall_score:.1f}/10", 
                                delta=f"{quality_score.improvement_potential:.1f} potential")
                    with col_b:
                        st.metric("Readability", f"{quality_score.readability:.1f}/10")
                    with col_c:
                        st.metric("Performance", f"{quality_score.performance:.1f}/10")
                    
                    # Display result
                    st.markdown(review_report)
                    
                    # Enhanced download options
                    col_dl1, col_dl2 = st.columns(2)
                    with col_dl1:
                        st.download_button(
                            "📥 Download Markdown",
                            data=review_report,
                            file_name=f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    with col_dl2:
                        # Create enhanced report with metadata
                        enhanced_report = f"""# Code Review Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Persona: {selected_persona}
Overall Quality: {quality_score.overall_score:.1f}/10

{review_report}

---
Generated with Empathetic Code Reviewer Pro
"""
                        st.download_button(
                            "📊 Download Enhanced Report",
                            data=enhanced_report,
                            file_name=f"enhanced_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                            mime="text/markdown",
                            use_container_width=True
                        )
                    
                    # Store results for analytics tab
                    st.session_state['last_quality_score'] = quality_score
                    st.session_state['last_analysis'] = reviewer.analyze_code_quality(
                        input_data['code_snippet'], input_data['review_comments']
                    )
                    
                except ValueError as e:
                    st.error(f"❌ Input Error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.write("Please check your API key and try again.")
            
            else:
                # Show informative placeholder
                if not api_key:
                    st.info("👈 Please enter your OpenAI API key in the sidebar to get started.")
                elif not json_input.strip():
                    st.info("👈 Please enter JSON input to generate a review.")
                else:
                    st.info("👈 Click 'Generate Empathetic Review' to transform your feedback!")
                    
                    # Show preview of what will happen
                    st.markdown("""
                    ### 🎯 What happens when you click generate:
                    1. **Language Detection** - Automatically identify your programming language
                    2. **Persona Application** - Apply your selected reviewer style
                    3. **Quality Analysis** - Calculate comprehensive quality metrics  
                    4. **Empathetic Transformation** - Convert harsh feedback to constructive guidance
                    5. **Resource Linking** - Add relevant documentation and best practices
                    6. **Export Options** - Download in multiple formats
                    """)
    
    with tab2:
        st.header("📊 Code Quality Analytics")
        
        if 'last_quality_score' in st.session_state and 'last_analysis' in st.session_state:
            quality_score = st.session_state['last_quality_score']
            analysis = st.session_state['last_analysis']
            
            # Quality metrics overview
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("📈 Quality Metrics Radar")
                fig_radar = create_quality_chart(quality_score)
                st.plotly_chart(fig_radar, use_container_width=True)
                
            with col2:
                st.subheader("🎯 Overall Score")
                fig_gauge = create_score_gauge(quality_score.overall_score)
                st.plotly_chart(fig_gauge, use_container_width=True)
            
            # Detailed breakdown
            st.subheader("📋 Detailed Analysis")
            
            col_a, col_b, col_c, col_d = st.columns(4)
            with col_a:
                st.metric("Readability", f"{quality_score.readability:.1f}/10", 
                         help="Code clarity and ease of understanding")
            with col_b:
                st.metric("Performance", f"{quality_score.performance:.1f}/10",
                         help="Efficiency and optimization opportunities")
            with col_c:
                st.metric("Maintainability", f"{quality_score.maintainability:.1f}/10",
                         help="Long-term code sustainability")
            with col_d:
                st.metric("Best Practices", f"{quality_score.best_practices:.1f}/10",
                         help="Adherence to coding standards")
            
            # Issue breakdown
            st.subheader("🔍 Issue Analysis")
            severity_data = analysis['severity_breakdown']
            
            if sum(severity_data.values()) > 0:
                # Create pie chart for severity distribution
                fig_pie = px.pie(
                    values=list(severity_data.values()),
                    names=list(severity_data.keys()),
                    title="Comment Severity Distribution",
                    color_discrete_map={
                        'harsh': '#ff4444',
                        'moderate': '#ffaa00', 
                        'neutral': '#44ff44'
                    }
                )
                st.plotly_chart(fig_pie, use_container_width=True)
                
                # Summary insights
                st.markdown(f"""
                <div class="quality-metrics">
                    <h4>🎯 Key Insights:</h4>
                    <ul>
                        <li><strong>Language Detected:</strong> {analysis['language'].title()}</li>
                        <li><strong>Total Issues:</strong> {analysis['total_issues']} comments</li>
                        <li><strong>Most Common Severity:</strong> {max(severity_data.keys(), key=lambda k: severity_data[k]).title()}</li>
                        <li><strong>Improvement Potential:</strong> {quality_score.improvement_potential:.1f} points</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info("🎉 No issues detected - excellent code quality!")
        else:
            st.info("📊 Generate a review first to see quality analytics here!")
            
            # Show sample analytics
            st.subheader("📋 Sample Analytics Preview")
            st.markdown("""
            After generating a review, you'll see:
            
            **📈 Visual Metrics**
            - Radar chart showing quality dimensions
            - Gauge chart for overall score
            - Pie chart for issue severity distribution
            
            **🔍 Detailed Insights**
            - Language detection results
            - Issue categorization and counts  
            - Improvement potential analysis
            - Trend tracking (coming soon)
            """)
    
    with tab3:
        st.header("📚 Resources & Examples")
        
        # Language-specific resources
        st.subheader("🌐 Language-Specific Resources")
        
        resource_tabs = st.tabs(["🐍 Python", "🟨 JavaScript", "☕ Java", "⚡ C++", "🔷 Go"])
        
        with resource_tabs[0]:  # Python
            st.markdown("""
            ### 📖 Python Best Practices
            
            **📝 Style & Conventions**
            - [PEP 8 - Style Guide](https://peps.python.org/pep-0008/)
            - [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
            - [Python Naming Conventions](https://peps.python.org/pep-0008/#naming-conventions)
            
            **⚡ Performance**
            - [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
            - [List Comprehensions Guide](https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions)
            
            **🔧 Tools**
            - [Black - Code Formatter](https://black.readthedocs.io/)
            - [Pylint - Static Analysis](https://pylint.org/)
            """)
        
        with resource_tabs[1]:  # JavaScript  
            st.markdown("""
            ### 📖 JavaScript Best Practices
            
            **📝 Style & Conventions**
            - [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
            - [MDN JavaScript Guidelines](https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Writing_style_guide/Code_style_guide/JavaScript)
            
            **⚡ Performance**
            - [JavaScript Performance Best Practices](https://developer.mozilla.org/en-US/docs/Learn/Performance/JavaScript)
            - [Async/Await Guide](https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Asynchronous/Async_await)
            
            **🔧 Modern Features**
            - [ES6 Features Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/New_in_JavaScript)
            - [JavaScript Modules](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Modules)
            """)
        
        with resource_tabs[2]:  # Java
            st.markdown("""
            ### 📖 Java Best Practices
            
            **📝 Style & Conventions**
            - [Google Java Style Guide](https://google.github.io/styleguide/javaguide.html)
            - [Oracle Code Conventions](https://www.oracle.com/java/technologies/javase/codeconventions-namingconventions.html)
            
            **⚡ Performance**
            - [Java Performance Tuning](https://docs.oracle.com/javase/8/docs/technotes/guides/performance/)
            - [Effective Java by Joshua Bloch](https://www.oracle.com/technical-resources/articles/java/bloch-effective-08-qa.html)
            
            **🔧 Concurrency**
            - [Java Concurrency Tutorial](https://docs.oracle.com/javase/tutorial/essential/concurrency/)
            """)
        
        with resource_tabs[3]:  # C++
            st.markdown("""
            ### 📖 C++ Best Practices
            
            **📝 Style & Guidelines**
            - [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines)
            - [Google C++ Style Guide](https://google.github.io/styleguide/cppguide.html)
            
            **⚡ Performance**
            - [C++ Performance Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#S-performance)
            - [Modern C++ Best Practices](https://github.com/cpp-best-practices/cppbestpractices)
            """)
        
        with resource_tabs[4]:  # Go
            st.markdown("""
            ### 📖 Go Best Practices
            
            **📝 Style & Conventions**
            - [Effective Go](https://golang.org/doc/effective_go.html)
            - [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
            
            **⚡ Performance**
            - [Go Performance Tips](https://github.com/golang/go/wiki/Performance)
            - [Go Memory Model](https://golang.org/ref/mem)
            """)
        
        # Example showcase
        st.subheader("📋 Example Transformations")
        
        example_showcase = st.selectbox(
            "Choose example to preview:",
            ["Python - List Processing", "JavaScript - Array Methods", "Java - Stream API"]
        )
        
        if example_showcase == "Python - List Processing":
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**❌ Before (Harsh)**")
                st.code("""
# Original comment:
"This is inefficient and badly written."
                """)
                
            with col2:
                st.markdown("**✅ After (Empathetic)**")
                st.code("""
# Empathetic version:
"Great start on the logic! For better performance
with large lists, we can optimize this using 
list comprehensions..."
                """)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem 0;'>
        <p><strong>Empathetic Code Reviewer Pro</strong> - Making code reviews more human</p>
        <p>Built with ❤️ for the developer community | 
        <a href='#'>📖 Documentation</a> | 
        <a href='#'>🐛 Report Issues</a> | 
        <a href='#'>⭐ Star on GitHub</a></p>
        <p><em>Version 2.0 - Now with multi-language support, AI personas, and quality analytics</em></p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    # Initialize session state
    if 'example_loaded' not in st.session_state:
        st.session_state['example_loaded'] = False
    
    main()