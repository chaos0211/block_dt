import hashlib
import json
import time
from uuid import uuid4

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        # 创建创世区块（链的起点，不是项目的起点）
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        创建一个新区块并添加到链中
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions, # 将交易池数据打包
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # 重置交易池
        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount, tx_type="TRANSFER", payload=None):
        """
        创建一个新交易到交易池
        :param tx_type: 交易类型，PROJECT_INIT 代表项目发布
        :param payload: 附加数据，用于存项目ID等元数据
        """
        transaction = {
            'id': str(uuid4()).replace('-', ''),
            'type': tx_type,
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'payload': payload or {},
            'timestamp': time.time(),
        }
        self.current_transactions.append(transaction)
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """生成区块的 SHA-256 哈希"""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """简单的 PoW 算法 (模拟)"""
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000" # 模拟挖矿难度

# 初始化一个全局单例
blockchain_instance = Blockchain()