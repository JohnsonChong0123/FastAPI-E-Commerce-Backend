# core/security.py
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

# Initialize the PasswordHash manager with multiple hashers.
# The first hasher in the list (Argon2) is used as the default for creating new hashes.
# Subsequent hashers (Bcrypt) are included to provide backward compatibility for legacy passwords.
password_hash = PasswordHash(
    hashers=[
        Argon2Hasher(),  # Primary hasher for all new and updated passwords
        BcryptHasher(),  # Supported for verifying existing Bcrypt passwords in the database
    ]
)

def hash_password(password: str) -> str:
    """
    Hashes a plaintext password using the default hasher (Argon2id).
    
    Args:
        password: The plaintext password to hash.
        
    Returns:
        The securely hashed password string.
    """
    if not password:
        raise ValueError("Password cannot be empty")
    return password_hash.hash(password)

def verify_password(password: str, hash: str) -> bool:
    """
    Verifies a plaintext password against a provided hash.
    
    The system automatically identifies the algorithm used (Argon2 or Bcrypt) 
    based on the hash prefix and verifies accordingly.
    
    Args:
        password: The plaintext password provided by the user.
        hash: The stored hash to compare against.
        
    Returns:
        True if the password matches the hash, False otherwise.
    """
    try:
        return password_hash.verify(password, hash)
    except Exception:
        # Returns False if the hash format is invalid or corrupted
        return False

def needs_upgrade(hash: str) -> bool:
    """
    Check if the hash needs to be updated.
    In pwdlib 0.3.0, we manually verify the prefix to determine 
    if it matches our primary hasher (Argon2).
    """
    
    return not str(hash).startswith("$argon2id$")