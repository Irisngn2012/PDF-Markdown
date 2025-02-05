from langchain_core.prompts import ChatPromptTemplate
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain_pydantic
from pydantic import BaseModel
from dotenv import load_dotenv
from agentic_chunker import AgenticChunker  # Your custom chunker class
import os

# Step 1: Load environment variables
load_dotenv()

# Initialize the language model
llm = ChatOpenAI(
    model="gpt-4-1106-preview",
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0,
)

# Define the Sentences schema for extraction
class Sentences(BaseModel):
    sentences: list[str]

# Create the extraction chain
extraction_chain = create_extraction_chain_pydantic(pydantic_schema=Sentences, llm=llm)

# File path to the essay
file_path = os.path.join(os.getcwd(), "uploads", "Thue_TNCN_chatbot_tuyennt25.txt")

# Treat entire paragraphs as single propositions
def get_propositions(paragraph):
    return paragraph.split("\n")  # Split the paragraph into sentences or lines

# Open and process the file
with open(file_path, "r", encoding="utf-8") as file:
    essay = file.read()

print(f"Loaded essay with length {len(essay)} characters")

# Split the essay into paragraphs
paragraphs = essay.split("\n\n")  # Assuming paragraphs are separated by double line breaks

# Initialize AgenticChunker
ac = AgenticChunker()

# Process paragraphs and extract propositions
essay_propositions = []
for para in paragraphs:
    print(f"Processing paragraph (first 100 chars): {para[:100]}")  # Debugging output
    propositions = get_propositions(para)  # Treat entire paragraph as a single unit
    print(f"Extracted {len(propositions)} propositions: {propositions}")
    essay_propositions.extend(propositions)  # Add to the list of all propositions

# Add extracted propositions to AgenticChunker
print(f"Adding {len(essay_propositions)} propositions to the chunker...")
ac.add_propositions(essay_propositions)  # Add all extracted propositions to the chunker

# Print the chunks created
print("Chunks after addition:")
ac.pretty_print_chunks()  # Display detailed chunks
ac.pretty_print_chunk_outline()  # Show chunk summary
print("Processing complete.")
