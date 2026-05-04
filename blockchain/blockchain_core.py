"""
Blockchain Core Implementation for ShieldDFL
Reputation-driven hybrid consensus for FL logging
"""
import hashlib
import json
import time
from typing import List, Dict, Optional
import logging

logger = logging.getLogger('shielddfl')


class Transaction:
    """Transaction class for blockchain"""
    def __init__(self, sender: str, recipient: str, data: Dict, timestamp: Optional[float] = None):
        self.sender = sender
        self.recipient = recipient
        self.data = data
        self.timestamp = timestamp or time.time()
        self.tx_hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate transaction hash"""
        tx_string = json.dumps({
            'sender': self.sender,
            'recipient': self.recipient,
            'data': self.data,
            'timestamp': self.timestamp
        }, sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'data': self.data,
            'timestamp': self.timestamp,
            'hash': self.tx_hash
        }


class Block:
    """In‑memory Block class for blockchain"""
    def __init__(
        self,
        index: int,
        transactions: List[Transaction],
        timestamp: float,
        previous_hash: str,
        nonce: int = 0,
        miner: str = "",
        reputation_scores: Dict = None
    ):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.miner = miner
        self.reputation_scores = reputation_scores or {}
        self.merkle_root = self.calculate_merkle_root()
        self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate block hash"""
        block_string = json.dumps({
            'index': self.index,
            'merkle_root': self.merkle_root,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'miner': self.miner,
            'reputation_scores': self.reputation_scores
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def calculate_merkle_root(self) -> str:
        """Calculate Merkle root of transactions"""
        if not self.transactions:
            return hashlib.sha256("empty".encode()).hexdigest()
        
        tx_hashes = [tx.tx_hash for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])
            
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i+1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            tx_hashes = new_hashes
        
        return tx_hashes[0]
    
    def to_dict(self) -> Dict:
        return {
            'index': self.index,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'hash': self.hash,
            'nonce': self.nonce,
            'merkle_root': self.merkle_root,
            'miner': self.miner,
            'reputation_scores': self.reputation_scores
        }


class Blockchain:
    """Blockchain implementation with reputation-driven PoW"""
    
    def __init__(self, difficulty: int = 4):
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.pending_transactions: List[Transaction] = []
        self.mining_reward = 10
        self.min_reputation = 0.5  # Minimum reputation to participate
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the genesis block"""
        genesis_block = Block(
            index=0,
            transactions=[],
            timestamp=time.time(),
            previous_hash="0" * 64,
            miner="Genesis"
        )
        self.chain.append(genesis_block)
        logger.info("Genesis block created")
    
    def get_latest_block(self) -> Block:
        """Get the latest block in the chain"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add transaction to pending pool"""
        if not transaction.sender or not transaction.recipient:
            logger.warning("Invalid transaction: missing sender or recipient")
            return False
        
        self.pending_transactions.append(transaction)
        logger.info(f"Transaction added: {transaction.tx_hash[:8]}...")
        return True
    
    def mine_pending_transactions(self, miner_address: str, miner_reputation: float) -> Optional[Block]:
        """
        Mine pending transactions into a new block.
        Uses reputation-based difficulty adjustment.
        """
        if miner_reputation < self.min_reputation:
            logger.warning(f"Miner {miner_address} has insufficient reputation: {miner_reputation}")
            return None
        
        if not self.pending_transactions:
            logger.info("No pending transactions to mine")
            return None
        
        new_block = Block(
            index=len(self.chain),
            transactions=self.pending_transactions.copy(),
            timestamp=time.time(),
            previous_hash=self.get_latest_block().hash,
            miner=miner_address,
            reputation_scores={miner_address: miner_reputation}
        )
        
        self.proof_of_work(new_block, miner_reputation)
        
        self.chain.append(new_block)
        self.pending_transactions = []
        
        reward_tx = Transaction(
            sender="Network",
            recipient=miner_address,
            data={'type': 'reward', 'amount': self.mining_reward, 'reputation': miner_reputation}
        )
        self.pending_transactions.append(reward_tx)
        
        logger.info(f"Block {new_block.index} mined by {miner_address} with reputation {miner_reputation}")
        return new_block
    
    def proof_of_work(self, block: Block, miner_reputation: float):
        """
        Proof of Work with reputation adjustment.
        Higher reputation = lower effective difficulty.
        """
        adjusted_difficulty = max(1, int(self.difficulty * (1 - miner_reputation * 0.5)))
        target = "0" * adjusted_difficulty
        
        while block.hash[:adjusted_difficulty] != target:
            block.nonce += 1
            block.hash = block.calculate_hash()
        
        logger.info(f"Block mined with nonce {block.nonce} (difficulty: {adjusted_difficulty})")
    
    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                logger.error(f"Invalid hash at block {current_block.index}")
                return False
            
            if current_block.previous_hash != previous_block.hash:
                logger.error(f"Invalid chain link at block {current_block.index}")
                return False
            
            if current_block.merkle_root != current_block.calculate_merkle_root():
                logger.error(f"Invalid Merkle root at block {current_block.index}")
                return False
        
        return True
    
    def get_balance(self, address: str) -> float:
        """Calculate balance for an address (mining rewards)"""
        balance = 0
        for block in self.chain:
            for tx in block.transactions:
                if tx.recipient == address and tx.data.get('type') == 'reward':
                    balance += tx.data.get('amount', 0)
        return balance
    
    def get_statistics(self) -> Dict:
        """Get blockchain statistics"""
        total_transactions = sum(len(block.transactions) for block in self.chain)
        return {
            'chain_length': len(self.chain),
            'total_transactions': total_transactions,
            'pending_transactions': len(self.pending_transactions),
            'difficulty': self.difficulty,
            'is_valid': self.is_chain_valid()
        }


class ReputationDrivenConsensus:
    """
    Hybrid Consensus Mechanism using Reputation.
    Combines PoW with reputation-weighted miner selection.
    """
    
    def __init__(self, blockchain: Blockchain, reputation_threshold: float = 0.5):
        self.blockchain = blockchain
        self.reputation_threshold = reputation_threshold
        self.validators: Dict[str, float] = {}  # address -> reputation
    
    def register_validator(self, address: str, reputation: float):
        """Register a validator with their reputation score"""
        if reputation >= self.reputation_threshold:
            self.validators[address] = reputation
            logger.info(f"Validator {address} registered with reputation {reputation}")
    
    def select_miner(self) -> Optional[str]:
        """Select miner based on weighted reputation"""
        if not self.validators:
            return None
        
        import random
        total_reputation = sum(self.validators.values())
        
        if total_reputation == 0:
            return random.choice(list(self.validators.keys()))
        
        r = random.uniform(0, total_reputation)
        current = 0
        for address, reputation in self.validators.items():
            current += reputation
            if r <= current:
                return address
        return list(self.validators.keys())[-1]
    
    def validate_block(self, block: Block, validator_reputation: float) -> bool:
        """Validate a block using reputation-weighted voting"""
        if not self.blockchain.is_chain_valid():
            return False
        
        validation_score = validator_reputation
        required_score = self.reputation_threshold
        return validation_score >= required_score
