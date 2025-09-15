import logging
from typing import List, Dict, Optional, Union
from langchain_ollama import OllamaLLM
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain.memory import ConversationBufferMemory

from ...query_definition import ResumeQueryService
from ...query_definition.config import QueryDefinitionConfig
from ..config import ChatConfig, LLMConfig, get_chat_config


logger = logging.getLogger(__name__)


class CareerChatService:
    """Career-focused chat service using LangChain with configurable LLM providers."""
    
    def __init__(self, config: Optional[ChatConfig] = None):
        if config is None:
            config = get_chat_config()
        
        self.config = config
        
        # Initialize chat LLM
        self.llm = self._create_llm(config.chat_llm)
        
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=config.memory_token_limit
        )
        
        # Initialize resume service with separate LLM config
        self.resume_service = self._create_resume_service(config.resume_llm)
        self.resume_analyzed = False
        
        # Career-focused system prompt
        self.system_prompt = """You are a helpful career advisor and job search assistant. Your role is to:

1. Help users with career guidance, job search strategies, and professional development
2. Analyze resumes and suggest relevant job opportunities
3. Provide advice on interview preparation, networking, and career transitions
4. Answer questions about industry trends, salary expectations, and skill development

IMPORTANT GUIDELINES:
- Stay focused on career and job-related topics only
- If asked about non-career topics, politely redirect to career matters
- Be encouraging and professional in your responses
- Provide actionable advice when possible
- Keep responses concise but helpful

If someone asks about topics unrelated to careers (like cooking, sports, general knowledge, etc.), respond with:
"I'm a career advisor focused on helping you with job search and professional development. Let's talk about your career goals instead! How can I help you with your job search or professional growth?"
"""
        
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ])
        
        self.chain = self.prompt_template | self.llm
    
    def _create_llm(self, llm_config: LLMConfig) -> Union[ChatOpenAI, OllamaLLM]:
        """Create LLM instance based on configuration."""
        if llm_config.provider == "openai":
            if not llm_config.api_key:
                raise ValueError("OpenAI API key is required but not provided")
            
            return ChatOpenAI(
                model=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                api_key=llm_config.api_key
            )
        elif llm_config.provider == "ollama":
            return OllamaLLM(
                model=llm_config.model,
                base_url=llm_config.base_url,
                temperature=llm_config.temperature,
                num_predict=llm_config.num_predict
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")
    
    def _create_resume_service(self, llm_config: LLMConfig) -> ResumeQueryService:
        """Create resume service with specified LLM configuration."""
        # Convert LLMConfig to QueryDefinitionConfig
        query_config = QueryDefinitionConfig(
            llm_provider=llm_config.provider,
            llm_model=llm_config.model,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens or 1000,
            openai_api_key=llm_config.api_key,
            ollama_base_url=llm_config.base_url,
            ollama_num_predict=llm_config.num_predict or 1000
        )
        
        return ResumeQueryService(query_config)
    
    def get_welcome_message(self) -> str:
        """Get the welcome message for new chat sessions."""
        return """👋 **Hello! I'm your Career Finding Assistant!**

I'm here to help you with:
• **Job search strategies** and opportunities
• **Resume analysis** and career guidance  
• **Interview preparation** and networking tips
• **Career transitions** and skill development

🎯 **Let's start by uploading your resume** so I can provide personalized career advice and suggest relevant job opportunities for you!

Or feel free to ask me any career-related questions. How can I help you today?"""
    
    def is_career_related(self, message: str) -> bool:
        """Check if the message is career-related using keyword matching."""
        career_keywords = [
            'job', 'career', 'resume', 'interview', 'work', 'employment', 'salary', 
            'skills', 'experience', 'position', 'opportunity', 'hiring', 'linkedin',
            'networking', 'professional', 'industry', 'company', 'application',
            'qualification', 'certification', 'promotion', 'manager', 'developer',
            'engineer', 'analyst', 'director', 'internship', 'freelance'
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in career_keywords)
    
    def process_resume(self, file_path: str) -> str:
        """Process uploaded resume and generate career insights."""
        try:
            # Use query_definition service to analyze resume
            queries = self.resume_service.process_resume_file(file_path)
            
            # Mark resume as analyzed
            self.resume_analyzed = True
            
            # Create a natural response with career insights
            response = f"""🎉 **Great! I've analyzed your resume.** Here's what I found:

**🎯 Your Career Sweet Spot:**
Based on your background, you're perfectly positioned for roles like {queries.primary_titles[0]} or {queries.primary_titles[1]}. Your experience in {queries.industry_focus.lower()} shows strong domain expertise that employers value.

**🚀 Future Opportunities:**
I also see exciting potential for you in emerging areas like {queries.secondary_titles[0]} and {queries.secondary_titles[1]}. These represent the next level of your career evolution.

**💡 Key Strengths:**
Your skills in {queries.skill_based_queries[0].lower()} position you well for {queries.seniority_level.lower()}-level roles in the current market.

**Next Steps:**
1. **Target your search** around these {len(queries.primary_titles)} primary role types
2. **Expand your horizons** by exploring the {len(queries.secondary_titles)} future-focused opportunities I identified
3. **Leverage your expertise** in {queries.industry_focus.lower()} for competitive advantage

What would you like to focus on first? I can help you with:
- Crafting targeted job search strategies
- Preparing for specific interview types
- Developing skills for future opportunities
- Building your professional network"""
            
            # Add to conversation memory
            self.memory.chat_memory.add_user_message("I uploaded my resume for analysis")
            self.memory.chat_memory.add_ai_message(response)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing resume: {e}")
            return f"❌ **Sorry, I encountered an error analyzing your resume:** {str(e)}\n\nPlease try uploading again or ask me other career questions!"
    
    def get_response(self, user_input: str) -> str:
        """Get chat response for user input."""
        try:
            # Check if the message is career-related
            if not self.is_career_related(user_input):
                return """🎯 **I'm a career advisor focused on helping you with job search and professional development.**

Let's talk about your career goals instead! I can help you with:
• Job search strategies and opportunities
• Resume optimization and career advice
• Interview preparation and networking
• Professional development and skill building

What career topic would you like to discuss? 💼"""
            
            # Get chat history
            chat_history = self.memory.chat_memory.messages
            
            # Generate response using the chain
            response = self.chain.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            
            # Extract content from response (handle both string and AIMessage)
            if hasattr(response, 'content'):
                # LangChain AIMessage object
                response_content = response.content
            elif isinstance(response, str):
                # Plain string response
                response_content = response
            elif hasattr(response, 'text'):
                # Some LLM responses have .text attribute
                response_content = response.text
            else:
                # Fallback to string conversion
                response_content = str(response)
            
            # Add to memory
            self.memory.chat_memory.add_user_message(user_input)
            self.memory.chat_memory.add_ai_message(response_content)
            
            return response_content
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "❌ **I'm having trouble right now.** Please try again or rephrase your question. Make sure Ollama is running for the best experience!"
    
    def clear_memory(self):
        """Clear conversation memory."""
        self.memory.clear()
        self.resume_analyzed = False