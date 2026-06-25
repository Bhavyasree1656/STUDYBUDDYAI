from database.database import (
    get_all_documents,
    get_document,
    delete_document,
    update_history_opened,
)


def get_history() -> list[dict]:
    return get_all_documents()


def load_document(doc_id: str) -> dict | None:
    return get_document(doc_id)


def remove_document(doc_id: str) -> None:
    delete_document(doc_id)


def record_opened(doc_id: str) -> None:
    update_history_opened(doc_id)
