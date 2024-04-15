from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def normal_prompt_process(raw: str, prompt_template: str):
    llm = ChatOpenAI(temperature=0.2)
    prompt = ChatPromptTemplate.from_messages([
        ("system","You are french language teacher."),
        ("user", "{input}")
    ])
    chain = prompt | llm
    response = chain.invoke({"input":prompt_template.format(key_word=raw)})
    return response.content