from fastapi import APIRouter, HTTPException, status

from indirectinject.engine.evaluator import RAGEvaluator
from indirectinject.engine.poisoner import TEMPLATES, embed_poison_into_document
from indirectinject.engine.vector_store import MemoryVectorStore
from indirectinject.models import (
    IngestRequest,
    PoisonTemplate,
    RAGQueryRequest,
    RAGSimulationResult,
)

router = APIRouter(prefix="/api/v1")
store = MemoryVectorStore()
evaluator = RAGEvaluator()

# Initialize with a default corporate document
_DEFAULT_DOC = (
    "Customer Support FAQ\n\n"
    "Returns and Refunds Policy:\n"
    "Customers may initiate a return within 30 calendar days of delivery. "
    "All returned items must be in their original packaging and accompanied "
    "by a proof of purchase receipt.\n\n"
    "Shipping and Handling:\n"
    "Standard delivery requires 3 to 5 business days. "
    "Expedited shipping is available at checkout.\n\n"
    "Account Security and Password Reset:\n"
    "Users can reset account credentials by visiting the account management portal and requesting "
    "a one-time passcode delivered to their registered email address."
)
store.add_document("customer_faq.txt", _DEFAULT_DOC)


@router.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "service": "IndirectInject"}


@router.get("/templates", response_model=list[PoisonTemplate])
def get_poison_templates():
    return list(TEMPLATES.values())


@router.get("/documents/chunks")
def list_chunks():
    return store.chunks


@router.post("/documents/ingest", status_code=status.HTTP_201_CREATED)
def ingest_document(request: IngestRequest):
    try:
        if request.poison_strategy:
            content, poison_indices = embed_poison_into_document(
                request.content,
                request.poison_strategy,
                request.custom_adversarial_instruction,
                request.trigger_keyword,
            )
            created = store.add_document(
                request.doc_name,
                content,
                poison_strategy=request.poison_strategy,
                poison_chunk_indices=poison_indices,
            )
        else:
            created = store.add_document(request.doc_name, request.content)

        return {
            "status": "ingested",
            "doc_name": request.doc_name,
            "chunks_created": len(created),
            "is_poisoned": request.poison_strategy is not None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/simulate", response_model=RAGSimulationResult)
def simulate_rag_query(request: RAGQueryRequest):
    retrieved = store.retrieve(request.user_query, top_k=request.top_k)
    return evaluator.execute_simulation(request, retrieved)


@router.post("/reset")
def reset_vector_store():
    store.clear()
    store.add_document("customer_faq.txt", _DEFAULT_DOC)
    return {"status": "reset", "total_chunks": len(store.chunks)}
