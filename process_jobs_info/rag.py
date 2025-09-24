'''
todo:
to connect with rag llm for resume matching
openai

'''


import json
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
import faiss
from openai import OpenAI
import os
import pickle

@dataclass
class Position:
    Idx: str
    title: str
    salary: str
    position: str
    experience: str
    degree: str
    tags: str
    describe: str
    company_name: str
    scale: str
    industry: str
    
    def to_searchable_text(self) -> str:
        """Convert position to searchable text for embeddings"""
        text_parts = [
            self.title,
            self.salary,
            self.position,
            self.experience,
            self.degree,
            self.tags,
            self.describe,
            self.company_name,
            self.scale,
            self.industry
        ]
        return " ".join(filter(None, text_parts))

class ResumeRAGMatcher:
    def __init__(self, embedding_model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG-based resume matcher
        
        Args:
            embedding_model_name: Name of the sentence transformer model
        """
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.positions: List[Position] = []
        self.position_embeddings = None
        self.faiss_index = None
        self.openai_client = OpenAI()  # Make sure to set OPENAI_API_KEY
        
    def load_positions_from_json(self, positions_file: str):
        """Load positions from JSON file with new format"""
        with open(positions_file, 'r', encoding='utf-8') as f:
            positions_data = json.load(f)
        
        self.positions = []
        for pos_data in positions_data:
            position = Position(
                Idx=pos_data.get('Idx', ''),
                title=pos_data.get('title', ''),
                salary=pos_data.get('salary', ''),
                position=pos_data.get('position', ''),
                experience=pos_data.get('experience', ''),
                degree=pos_data.get('degree', ''),
                tags=pos_data.get('tags', ''),
                describe=pos_data.get('describe', ''),
                company_name=pos_data.get('company_name', ''),
                scale=pos_data.get('scale', ''),
                industry=pos_data.get('industry', '')
            )
            self.positions.append(position)
        
        print(f"Loaded {len(self.positions)} positions")
    
    def build_vector_index(self):
        """Build FAISS vector index from position data"""
        print("Building vector index...")
        
        # Generate embeddings for all positions
        position_texts = [pos.to_searchable_text() for pos in self.positions]
        self.position_embeddings = self.embedding_model.encode(position_texts)
        
        # Build FAISS index
        dimension = self.position_embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.position_embeddings)
        self.faiss_index.add(self.position_embeddings.astype('float32'))
        
        print(f"Built FAISS index with {self.faiss_index.ntotal} positions")
    
    def save_index(self, filepath: str):
        """Save the FAISS index and position data to files"""
        # Save FAISS index
        faiss.write_index(self.faiss_index, f"{filepath}.index")
        
        # Save position embeddings
        np.save(f"{filepath}.embeddings.npy", self.position_embeddings)
        
        # Save positions list
        with open(f"{filepath}.positions.pkl", 'wb') as f:
            pickle.dump(self.positions, f)
        
        print(f"Saved index to {filepath}.*")
    
    def load_index(self, filepath: str):
        """Load the FAISS index and position data from files"""
        # Load FAISS index
        self.faiss_index = faiss.read_index(f"{filepath}.index")
        
        # Load position embeddings
        self.position_embeddings = np.load(f"{filepath}.embeddings.npy")
        
        # Load positions list
        with open(f"{filepath}.positions.pkl", 'rb') as f:
            self.positions = pickle.load(f)
        
        print(f"Loaded index from {filepath}.* with {len(self.positions)} positions")
    
    def add_positions_from_json(self, new_positions_file: str):
        """Add new positions from JSON file to existing index"""
        # Load new positions
        with open(new_positions_file, 'r', encoding='utf-8') as f:
            new_positions_data = json.load(f)
        
        new_positions = []
        for pos_data in new_positions_data:
            position = Position(
                Idx=pos_data.get('Idx', ''),
                title=pos_data.get('title', ''),
                salary=pos_data.get('salary', ''),
                position=pos_data.get('position', ''),
                experience=pos_data.get('experience', ''),
                degree=pos_data.get('degree', ''),
                tags=pos_data.get('tags', ''),
                describe=pos_data.get('describe', ''),
                company_name=pos_data.get('company_name', ''),
                scale=pos_data.get('scale', ''),
                industry=pos_data.get('industry', '')
            )
            new_positions.append(position)
        
        # Generate embeddings for new positions
        new_texts = [pos.to_searchable_text() for pos in new_positions]
        new_embeddings = self.embedding_model.encode(new_texts)
        
        # Add to existing positions and embeddings
        self.positions.extend(new_positions)
        
        if self.position_embeddings is None:
            self.position_embeddings = new_embeddings
        else:
            self.position_embeddings = np.vstack([self.position_embeddings, new_embeddings])
        
        # Rebuild the index
        dimension = self.position_embeddings.shape[1]
        self.faiss_index = faiss.IndexFlatIP(dimension)
        faiss.normalize_L2(self.position_embeddings)
        self.faiss_index.add(self.position_embeddings.astype('float32'))
        
        print(f"Added {len(new_positions)} new positions, total now {len(self.positions)}")
    
    def extract_resume_features(self, resume_json: Dict[str, Any]) -> str:
        """Extract searchable text from resume JSON with new format"""
        features = []
        
        # Basic info
        if 'personal_information' in resume_json:
            personal = resume_json['personal_information']
            features.append(personal.get('full_name', ''))
            features.append(personal.get('location', ''))
        
        # Professional summary
        if 'professional_summary' in resume_json:
            features.append(resume_json['professional_summary'])
        
        # Skills
        if 'skills' in resume_json:
            skills = resume_json['skills']
            if 'technical' in skills:
                features.extend(skills['technical'])
            if 'soft' in skills:
                features.extend(skills['soft'])
        
        # Work experience
        if 'work_experience' in resume_json:
            for exp in resume_json['work_experience']:
                if isinstance(exp, dict):
                    features.append(exp.get('title', ''))
                    features.append(exp.get('company', ''))
                    features.append(exp.get('description', ''))
        
        # Education
        if 'education' in resume_json:
            for edu in resume_json['education']:
                if isinstance(edu, dict):
                    features.append(edu.get('degree', ''))
                    features.append(edu.get('field', ''))
                    features.append(edu.get('school', ''))
                    features.append(edu.get('description', ''))
        
        # Certifications
        if 'certifications' in resume_json:
            for cert in resume_json['certifications']:
                if isinstance(cert, dict):
                    features.append(cert.get('name', ''))
                else:
                    features.append(str(cert))
        
        # Projects
        if 'projects' in resume_json:
            for proj in resume_json['projects']:
                if isinstance(proj, dict):
                    features.append(proj.get('name', ''))
                    features.append(proj.get('description', ''))
        
        return " ".join(filter(None, [str(f) for f in features]))
    
    def rag_filter_positions(self, resume_json: Dict[str, Any], n: int = 20) -> List[Position]:
        """
        Use RAG to filter top n matching positions
        
        Args:
            resume_json: Resume data as JSON
            n: Number of positions to return
            
        Returns:
            List of top n matching positions
        """
        if self.faiss_index is None:
            raise ValueError("Vector index not built. Call build_vector_index() first.")
        
        # Extract resume features and create embedding
        resume_text = self.extract_resume_features(resume_json)
        resume_embedding = self.embedding_model.encode([resume_text])
        faiss.normalize_L2(resume_embedding)
        
        # Search for similar positions
        scores, indices = self.faiss_index.search(resume_embedding.astype('float32'), n)
        
        # Return top matching positions with scores
        top_positions = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            position = self.positions[idx]
            # Add similarity score as attribute
            position.similarity_score = float(score)
            top_positions.append(position)
        
        return top_positions
    
    def match_resume_to_positions(self, resume_json: Dict[str, Any], n: int = 5) -> List[Dict[str, Any]]:
        """
        Match resume to positions and return top n matches
        
        Args:
            resume_json: Resume data as JSON
            n: Number of positions to return
            
        Returns:
            List of top n matching positions as JSON
        """
        print(f"Matching resume to top {n} positions...")
        candidate_positions = self.rag_filter_positions(resume_json, n)
        
        # Convert to JSON format
        result = []
        for pos in candidate_positions:
            pos_dict = asdict(pos)
            # Remove the similarity_score if it's not needed in final output
            if hasattr(pos, 'similarity_score'):
                pos_dict['similarity_score'] = getattr(pos, 'similarity_score', 0)
            result.append(pos_dict)
        
        return result

# 封装函数
def get_matched_positions(resume_json: Dict[str, Any], n: int = 5, 
                         index_path: str = "position_index") -> List[Dict[str, Any]]:
    """
    输入简历JSON和需要返回的岗位数量n，输出匹配的n个岗位JSON信息
    
    Args:
        resume_json: 简历JSON数据
        n: 需要返回的岗位数量
        index_path: 索引文件路径（不含扩展名）
        
    Returns:
        匹配的岗位JSON列表
    """
    # 初始化匹配器
    matcher = ResumeRAGMatcher()
    
    # 检查是否存在保存的索引
    if os.path.exists(f"{index_path}.index"):
        print("Loading existing index...")
        matcher.load_index(index_path)
    else:
        print("No existing index found. Please build index first.")
        return []
    
    # 进行匹配
    return matcher.match_resume_to_positions(resume_json, n)

# 构建索引的函数
def build_position_index(positions_file: str, index_path: str = "position_index"):
    """
    从JSON文件构建职位索引并保存
    
    Args:
        positions_file: 职位JSON文件路径
        index_path: 索引保存路径（不含扩展名）
    """
    matcher = ResumeRAGMatcher()
    matcher.load_positions_from_json(positions_file)
    matcher.build_vector_index()
    matcher.save_index(index_path)
    print("Index built and saved successfully.")

# 添加新职位到索引的函数
def add_to_position_index(new_positions_file: str, index_path: str = "position_index"):
    """
    添加新职位到现有索引
    
    Args:
        new_positions_file: 新职位JSON文件路径
        index_path: 索引路径（不含扩展名）
    """
    matcher = ResumeRAGMatcher()
    matcher.load_index(index_path)
    matcher.add_positions_from_json(new_positions_file)
    matcher.save_index(index_path)
    print("New positions added to index successfully.")

# 示例使用
if __name__ == "__main__":
    # 首先构建索引（只需要执行一次）
    build_position_index("job_data_city.json")
    
    # 示例简历数据
    example_resume = {
        "personal_information": {
            "full_name": "简豪",
            "email": "1367919489@qq.com",
            "phone_number": "17823672615",
            "location": "重庆",
            "linkedin_url": "",
            "portfolio_url": "https://github.com/dwdwqfwe"
        },
        "professional_summary": "",
        "work_experience": [],
        "education": [
            {
                "degree": "",
                "school": "重庆交通大学",
                "location": "重庆 (推断)",
                "start_date": "2022-09",
                "end_date": "2026-09",
                "is_current": True,
                "description": []
            }
        ],
        "skills": {
            "technical": [
                "c/c++",
                "现代c++编程",
                "shell",
                "python",
                "goland",
                "linux操作系统",
                "socket网络编程",
                "tcp协议",
                "udp协议",
                "git",
                "cmake",
                "sql",
                "关系型数据库内核开发",
                "Mysql",
                "设计模式 (单例模式, 工厂模式)"
            ],
            "soft": [],
            "languages": []
        },
        "certifications": [
            {
                "name": "CTE-4",
                "issuing_organization": "",
                "issue_date": "",
                "expiration_date": "",
                "credential_url": ""
            }
        ],
        "projects": [
            {
                "name": "Bustub数据库",
                "description": "基于c++17实现的关系型行存储数据库，支持完整数据库的优化器，存储，查询，删除与更新，以及事务功能。\n基于LRU-K算法实现了数据库缓冲池管理，并以此算法进行实现了存储页的替换，驱逐，并利用异步io提高了并发效率.\n利用ExtendibleHash实现了数据库的非聚簇索引,支持并发的索引查询与插入操作.\n实现了常用算子，如SeqScan,IndexScan,Insert,Update,Delete,实现了Join链接，ORDERBY+LIMIT\n基于火山模型实现了数据库的计算流水线，在优化器方面把NLJ优化为了HashJoin,SeqScan优化为IndexScan.\n基于时间戳与undo_log日志实现了多版本控制MVCC，对事务实现SNAPSHOTISOLATION隔离级别，为事务和tuple添加时间戳进行事务的隔离级别和控制和写写冲突，并添加了垃圾回收机制回收无用的历史tuple.",
                "start_date": "",
                "end_date": "",
                "project_url": ""
            },
            {
                "name": "基于RISC-V指令架构的操作系统内核（Mit6.828)",
                "description": "本项目基于xv6操作系统对其中的系统调用，内存管理，进程管理，文件系统等模板进行扩展和优化。\n增加一些新的系统调用，如sys_mmap将文件描述符对应文件映射到系统空间，sys__unmmap释放物理页面并将脏页刷新回磁盘等系统调用.\n添加了延迟分配和fork的COW机制来提高效率，pagefault时才进行内存分配.\n修改了创建进程时的页表内存分配，为xv6内核页表添加用户页表项，因此可以在内核状态直接访问用户虚拟地址所对应的物理地址.\n在inode添加多级索引，增加通过单个inode可以访问的数据块量，从而增加单个文件最大容量，增添了软连接",
                "start_date": "",
                "end_date": "",
                "project_url": ""
            }
        ]
    }
    
    # 获取匹配的职位
    matched_positions = get_matched_positions(example_resume, n=5)
    print(f"Found {len(matched_positions)} matching positions")
    
    # 输出结果
    for i, pos in enumerate(matched_positions, 1):
        print(f"\n{i}. {pos['title']} at {pos['company_name']}")
        print(f"   Similarity Score: {pos.get('similarity_score', 0):.3f}")
        print(f"   Location: {pos['position']}")
        print(f"   Salary: {pos['salary']}")