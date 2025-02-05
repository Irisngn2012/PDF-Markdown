from langchain.output_parsers.openai_tools import JsonOutputToolsParser
from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain.chains import create_extraction_chain_pydantic
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain import hub
from agentic_chunker import AgenticChunker  # Import your AgenticChunker implementation
import os

# Step 1: File Path Setup
base_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(base_dir, "uploads", "Thue_TNCN_chatbot_tuyennt25.txt")

# Step 2: Load the LangChain Object
obj = hub.pull("wfh/proposal-indexing")
llm = ChatOpenAI(
    model="gpt-4-1106-preview",
    openai_api_key=os.getenv("OPENAI_API_KEY", "your-openai-api-key"),
)

# Step 3: Define the Sentences Schema
class Sentences(BaseModel):
    sentences: list[str]

# Step 4: Create the Extraction Chain
extraction_chain = create_extraction_chain_pydantic(pydantic_schema=Sentences, llm=llm)

# Step 5: Define the get_propositions Function
def get_propositions(text):
    prompt = ChatPromptTemplate.from_messages(
        [("user", "{input}")]
    )
    runnable = prompt | llm
    runnable_output = runnable.invoke({"input": text}).content

    # Use extraction chain to extract propositions
    result = extraction_chain.invoke(runnable_output)
    print(f"Extraction result: {result}")
    if not isinstance(result, dict):
        return []

    # 'text' should be a list with one Sentences object
    text_list = result.get("text", [])
    if not text_list:
        print("No text extracted")
        return []

    # The first item is a `Sentences` object with `.sentences`
    first_item = text_list[0]
    if not first_item or not hasattr(first_item, "sentences"):
        print("No sentences in first item")
        return []

    # Retrieve the sentences
    propositions = first_item.sentences
    print(f"Extracted {len(propositions)} propositions")
    return propositions

with open(file_path, "r", encoding="utf-8") as file:
    essay = file.read()
print(f"Loaded essay with length {len(essay)}")


paragraphs = essay.split("\n\n")

ac = AgenticChunker()

essay_propositions = []
for para in paragraphs:
    print(f"Processing paragraph (first 100 chars): {para[:100]}")
    propositions = get_propositions(para)  # Save the result in `propositions`
    print(f"Extracted {len(propositions)} propositions: {propositions}")
    essay_propositions.extend(propositions)  # Append to `essay_propositions`

print(f"Adding {len(essay_propositions)} propositions to the chunker")
ac.add_propositions(essay_propositions)
print("Chunks after addition:")
ac.pretty_print_chunks()
ac.pretty_print_chunk_outline()
print("Done")