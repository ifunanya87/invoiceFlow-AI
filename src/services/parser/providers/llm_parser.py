# import os
# import logging
# from typing import Any, Dict
# from dotenv import load_dotenv


# from ..interface import BaseParser, InvoiceData

# from langchain_openai import ChatOpenAI
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_core.pydantic_v1 import BaseModel, Field
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.prompts import PromptTemplate

# logger = logging.getLogger(__name__)


# # Load .env automatically if API key not in environment
# if not os.getenv("OPENAI_API_KEY"):
#     load_dotenv()
#     if not os.getenv("OPENAI_API_KEY"):
#         raise ValueError("OPENAI_API_KEY not set in environment or .env file")

# # Pydantic schema
# class Document(BaseModel):
#     invoice_id: str = Field(description="Invoice ID or number")
#     vendor_name: str = Field(description="Vendor or company name")
#     total_amount: float = Field(description="Total amount on the invoice")
#     invoice_date: str = Field(description="Invoice date (YYYY-MM-DD)")
#     summary: str = Field(description="Short summary of the invoice")


# # LLM parser provider
# class LLMParser(BaseParser):
#     """
#     Parser provider that uses an OpenAI/ChatOpenAI LLM
#     to convert raw text into structured invoice data.
#     """

#     def __init__(self, model_name: str = "gpt-4o-mini"):
#         try:
#             self.llm = ChatOpenAI(model=model_name, openai_api_key=os.getenv("OPENAI_API_KEY"))
#             self.output_parser = JsonOutputParser(pydantic_object=Document)

#             # Prompt
#             self.prompt = PromptTemplate(
#                 template=(
#                     "Extract structured invoice information.\n"
#                     "{format_instructions}\n"
#                     "Raw text:\n{context}\n"
#                 ),
#                 input_variables=["context"],
#                 partial_variables={
#                     "format_instructions": self.output_parser.get_format_instructions()
#                 },
#             )

#             # Build chain: Prompt → LLM → JSON parser
#             self.chain = self.prompt | self.llm | self.output_parser

#             logger.info(f"[LLMParser] Model '{model_name}' initialized successfully.")

#         except Exception as e:
#             logger.error(f"[LLMParser] Failed to initialize model: {e}")
#             raise


#     def parse(self, raw_text: str) -> InvoiceData:
#         """Parse raw OCR text with the LLM into structured invoice data."""

#         raw_text = raw_text.strip()  # remove whitespace first

#         if not raw_text:
#             return {"error": "No text provided", "raw_text_length": 0}


#         try:
#             data = self.chain.invoke({"context": raw_text})
#             invoice_dict = data.dict() if hasattr(data, "dict") else dict(data)

#             # Include raw text length
#             invoice_dict["raw_text_length"] = len(raw_text)

#             return invoice_dict

#         except Exception as e:
#             logger.error(f"[LLMParser] Parsing failed: {e}")
#             return {
#                 "error": f"LLM parsing failed: {str(e)}",
#                 "invoice_id": None,
#                 "vendor_name": None,
#                 "total_amount": None,
#                 "invoice_date": None,
#                 "summary": None,
#                 "raw_text_length": len(raw_text),
#             }
