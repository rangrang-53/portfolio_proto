import os
from typing import List, Dict, Any
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

class VectorStore:
    """Pinecone 벡터 저장소를 사용한 텍스트 검색 클래스"""
    
    def __init__(self, index_name: str = "pdf-qa-index"):
        """
        Args:
            index_name: Pinecone 인덱스 이름
        """
        self.index_name = index_name
        self.api_key = os.getenv("PINECONE_API_KEY")
        
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY가 설정되지 않았습니다.")
        
        # Pinecone 클라이언트 초기화
        self.pc = Pinecone(api_key=self.api_key)
        
        # 임베딩 모델 초기화 (한국어 지원 모델)
        self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    
    def create_index(self, dimension: int = 384):
        """Pinecone 인덱스를 생성합니다."""
        try:
            # 인덱스가 이미 존재하는지 확인
            if self.index_name in self.pc.list_indexes().names():
                print(f"인덱스 '{self.index_name}'가 이미 존재합니다.")
                return
            
            # 인덱스 생성
            self.pc.create_index(
                name=self.index_name,
                dimension=dimension,
                metric="cosine"
            )
            print(f"인덱스 '{self.index_name}'가 생성되었습니다.")
            
        except Exception as e:
            print(f"인덱스 생성 중 오류 발생: {str(e)}")
    
    def delete_index(self):
        """Pinecone 인덱스를 삭제합니다."""
        try:
            if self.index_name in self.pc.list_indexes().names():
                self.pc.delete_index(self.index_name)
                print(f"인덱스 '{self.index_name}'가 삭제되었습니다.")
            else:
                print(f"인덱스 '{self.index_name}'가 존재하지 않습니다.")
        except Exception as e:
            print(f"인덱스 삭제 중 오류 발생: {str(e)}")
    
    def get_index(self):
        """Pinecone 인덱스를 가져옵니다."""
        try:
            return self.pc.Index(self.index_name)
        except Exception as e:
            print(f"인덱스 접근 중 오류 발생: {str(e)}")
            return None
    
    def add_text(self, text: str, metadata: Dict[str, Any] = None):
        """
        텍스트를 벡터 저장소에 추가합니다.
        
        Args:
            text: 저장할 텍스트
            metadata: 메타데이터 (선택사항)
        """
        try:
            index = self.get_index()
            if not index:
                return
            
            # 텍스트를 임베딩으로 변환
            embedding = self.embedding_model.encode(text).tolist()
            
            # 메타데이터 준비
            if metadata is None:
                metadata = {}
            
            # 벡터 저장소에 추가
            index.upsert(
                vectors=[{
                    "id": metadata.get("chunk_id", f"chunk_{len(metadata)}"),
                    "values": embedding,
                    "metadata": {
                        "text": text,
                        **metadata
                    }
                }]
            )
            
        except Exception as e:
            print(f"텍스트 추가 중 오류 발생: {str(e)}")
    
    def search_similar_text(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        쿼리와 유사한 텍스트를 검색합니다.
        
        Args:
            query: 검색 쿼리
            top_k: 반환할 결과 수 (기본값: 5로 증가)
            
        Returns:
            유사한 텍스트들의 리스트
        """
        try:
            index = self.get_index()
            if not index:
                return []
            
            # 쿼리를 임베딩으로 변환
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # 유사한 벡터 검색
            results = index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True
            )
            
            # 결과를 리스트로 변환 (필터링 없이 모든 결과 포함)
            similar_texts = []
            for match in results.matches:
                similar_texts.append({
                    "chunk_id": match.id,
                    "text": match.metadata.get("text", ""),
                    "score": match.score,
                    "metadata": match.metadata
                })
            
            # 디버깅을 위한 로그 추가
            print(f"검색 결과: {len(similar_texts)}개 반환됨")
            for i, text in enumerate(similar_texts):
                print(f"  결과 {i+1} (점수: {text['score']:.3f}): {text['text'][:100]}...")
            
            return similar_texts
            
        except Exception as e:
            print(f"텍스트 검색 중 오류 발생: {str(e)}")
            return []
    
    def clear_all_vectors(self):
        """모든 벡터를 삭제합니다."""
        try:
            index = self.get_index()
            if not index:
                return
            
            # 인덱스의 모든 벡터 삭제
            index.delete(delete_all=True)
            print("모든 벡터가 삭제되었습니다.")
            
        except Exception as e:
            print(f"벡터 삭제 중 오류 발생: {str(e)}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """인덱스 통계를 반환합니다."""
        try:
            index = self.get_index()
            if not index:
                return {}
            
            stats = index.describe_index_stats()
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
            
        except Exception as e:
            print(f"인덱스 통계 조회 중 오류 발생: {str(e)}")
            return {} 