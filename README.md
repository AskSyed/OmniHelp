# OmniHelp
Intelligent Customer Support Platform


1. The system consists of two different pipelines

   A. Unstructured Path (Product Manuals)
      Ingest PDFs in Vector Database, so that it can be used by LLM for RAG.

   B. Structured Path (Order Management)
      SQLExpress (Relational Database) to save and retrieve information about orders related to products.

2. The system has a UI which will take in product manuals and a database as an input.

3. For sample data Dell laptops product manuals can be used. This is the link for manuals https://dl.dell.com/content/manual34122770-latitude-3480-owner-s-manual.pdf?language=en-us.
