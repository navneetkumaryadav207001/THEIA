from hashlib import sha256
def handle_empty_sha(hash:str,raw:bytes) -> None:
    if hash == "":
        hash = sha256(raw).hexdigest()
    return hash