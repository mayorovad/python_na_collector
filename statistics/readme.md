В WireShark прописывать фильтр:

	tcp.port == 2463

ИЛИ

	tcp.port == 2463 && data.len > 0
