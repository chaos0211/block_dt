import uuid
from sqlalchemy.orm import Session
from .models import Project, ProjectStatus
from .blockchain_core import blockchain_instance


class ProjectService:

    @staticmethod
    def create_project_proposal(db: Session, data):
        """
        第一步：用户提交项目，生成密钥，存入DB，推入交易池
        """
        # 1. 生成项目专属钱包地址 (模拟)
        project_address = "0x" + uuid.uuid4().hex
        project_private_key = uuid.uuid4().hex

        # 2. 存入 MySQL (状态: Pending)
        new_project = Project(
            title=data.title,
            description=data.description,
            target_amount=data.target_amount,
            wallet_address=project_address,
            private_key=project_private_key,
            status=ProjectStatus.PENDING
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        # 3. 构造“创世交易” (Project Initialization Transaction)
        # 发送者为 "SYSTEM_GENESIS"，接收者为项目地址
        blockchain_instance.new_transaction(
            sender="SYSTEM_GENESIS",
            recipient=project_address,
            amount=0,
            tx_type="PROJECT_INIT",
            payload={
                "project_id": new_project.id,
                "project_title": new_project.title
            }
        )

        return new_project


class MiningService:

    @staticmethod
    def mine_block_and_sync_state(db: Session):
        """
        第二步：手动打包区块，并同步更新数据库状态
        """
        blockchain = blockchain_instance

        # 1. 如果没有交易，也可以挖空块，或者选择不挖
        if not blockchain.current_transactions:
            return {"message": "No transactions to mine", "activated": []}

        # 2. 运行工作量证明 (PoW)
        last_block = blockchain.last_block
        last_proof = last_block['proof']
        proof = blockchain.proof_of_work(last_proof)

        # 3. 构造新区块 (此时 current_transactions 被打包进 block)
        # 注意：在 new_block 调用前，我们需要暂存一下 transactions 用于后续分析
        transactions_to_mine = list(blockchain.current_transactions)
        block = blockchain.new_block(proof)

        # 4. 【核心逻辑】扫描刚刚打包的交易，更新数据库
        activated_project_ids = []

        for tx in transactions_to_mine:
            # 识别项目初始化交易
            if tx.get('type') == "PROJECT_INIT":
                payload = tx.get('payload', {})
                p_id = payload.get('project_id')

                if p_id:
                    # 查找数据库并更新状态为 Active
                    project = db.query(Project).filter(Project.id == p_id).first()
                    if project and project.status == ProjectStatus.PENDING:
                        project.status = ProjectStatus.ACTIVE
                        db.add(project)
                        activated_project_ids.append(p_id)

        # 提交数据库更改
        if activated_project_ids:
            db.commit()

        return {
            "message": "New Block Forged",
            "index": block['index'],
            "transactions": len(block['transactions']),
            "activated_projects": activated_project_ids
        }