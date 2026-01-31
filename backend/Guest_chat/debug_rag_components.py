import os
import pickle
from pathlib import Path
import numpy as np

def debug_rag_components():
    
    print("🔍 Debugging RAG Components")
    print("=" * 50)
    
    base_dir = Path(__file__).resolve().parent
    model_dir = base_dir / "model"
    

    faiss_path = model_dir / "corpus.index"
    print(f"\n1️⃣ FAISS Index: {faiss_path}")
    print(f"   Exists: {os.path.exists(faiss_path)}")
    
    if os.path.exists(faiss_path):
        try:
            file_size = os.path.getsize(faiss_path)
            print(f"   Size: {file_size:,} bytes")
            
          
            import faiss as faiss_lib
            
            
            index = faiss_lib.read_index(str(faiss_path))

            print(f"   ✅ FAISS index loaded successfully")
            print(f"   Documents: {index.ntotal}")
            print(f"   Dimension: {index.d}")
            print(f"   Index type: {type(index)}")
        except Exception as e:
            print(f"   ❌ FAISS load error: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
    
  
    corpus_path = os.path.join(model_dir, "corpus.pkl")
    print(f"\n2️⃣ Corpus: {corpus_path}")
    print(f"   Exists: {os.path.exists(corpus_path)}")
    
    if os.path.exists(corpus_path):
        try:
            file_size = os.path.getsize(corpus_path)
            print(f"   Size: {file_size:,} bytes")
            
        
            with open(corpus_path, 'rb') as f:
                corpus = pickle.load(f)
            
            print(f"   ✅ Corpus loaded successfully")
            print(f"   Type: {type(corpus)}")
            print(f"   Length: {len(corpus)}")
            if len(corpus) > 0:
                print(f"   Sample: {corpus[0][:100]}...")
                
            
            import faiss as faiss_lib
            try:
                index = faiss_lib.read_index(str(faiss_path))

                if len(corpus) == index.ntotal:
                    print(f"   ✅ Corpus-FAISS size match: {len(corpus)} documents")
                else:
                    print(f"   ⚠️ Size mismatch - Corpus: {len(corpus)}, FAISS: {index.ntotal}")
            except:
                pass
                
        except Exception as e:
            print(f"   ❌ Corpus load error: {e}")
    
  
    retriever_path = os.path.join(model_dir, "retriever_vimed_finetuned")
    print(f"\n3️⃣ Retriever: {retriever_path}")
    print(f"   Exists: {os.path.exists(retriever_path)}")
    
    if os.path.exists(retriever_path):
        try:
            files = os.listdir(retriever_path)
            print(f"   Files: {files}")
            
          
            config_file = os.path.join(retriever_path, "config.json")
            if os.path.exists(config_file):
                print(f"   ✅ config.json exists")
                
               
                import json
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print(f"   Model type: {config.get('model_type', 'unknown')}")
                print(f"   Hidden size: {config.get('hidden_size', 'unknown')}")
            
            model_file = os.path.join(retriever_path, "pytorch_model.bin")
            safetensors_file = os.path.join(retriever_path, "model.safetensors")
            
            if os.path.exists(model_file):
                print(f"   ✅ pytorch_model.bin exists")
                file_size = os.path.getsize(model_file)
                print(f"   Model size: {file_size:,} bytes")
            elif os.path.exists(safetensors_file):
                print(f"   ✅ model.safetensors exists")
                file_size = os.path.getsize(safetensors_file)
                print(f"   Model size: {file_size:,} bytes")
            else:
                print(f"   ❌ No model weights found")
                
            
            print(f"   🧪 Testing retriever loading...")
            try:
                from transformers import AutoTokenizer, AutoModel
                
                tokenizer = AutoTokenizer.from_pretrained(
                    retriever_path,
                    local_files_only=True
                )
                print(f"   ✅ Tokenizer loaded successfully")
                print(f"   Vocab size: {tokenizer.vocab_size}")
                
                model = AutoModel.from_pretrained(
                    retriever_path,
                    local_files_only=True
                )
                print(f"   ✅ Model loaded successfully")
                print(f"   Model type: {type(model)}")
                
            except Exception as e:
                print(f"   ❌ Retriever loading error: {e}")
                
        except Exception as e:
            print(f"   ❌ Retriever check error: {e}")
    
   
    print(f"\n4️⃣ Testing imports...")
    try:
        import torch
        print(f"   ✅ PyTorch: {torch.__version__}")
        
        import transformers
        print(f"   ✅ Transformers: {transformers.__version__}")
        
        import faiss as faiss_lib
        print(f"   ✅ FAISS available")
        
        import numpy
        print(f"   ✅ NumPy: {numpy.__version__}")
        
     
        print(f"   🧪 Testing FAISS functionality...")
        test_vectors = np.random.random((10, 768)).astype('float32')
        faiss_lib.normalize_L2(test_vectors)
        
        index = faiss_lib.IndexFlatIP(768)
        index.add(test_vectors)
        
        query = np.random.random((1, 768)).astype('float32')
        faiss_lib.normalize_L2(query)
        
        scores, indices = index.search(query, 3)
        print(f"   ✅ FAISS test successful")
        
    except Exception as e:
        print(f"   ❌ Import/test error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

   
    print(f"\n5️⃣ Testing complete RAG pipeline...")
    try:
        
        import faiss as faiss_lib
        from transformers import AutoTokenizer, AutoModel
        
       
        with open(corpus_path, 'rb') as f:
            corpus = pickle.load(f)
        print(f"   ✅ Corpus loaded: {len(corpus)} documents")
        
        
        index = faiss_lib.read_index(str(faiss_path))
        print(f"   ✅ FAISS loaded: {index.ntotal} vectors")
        
        
        tokenizer = AutoTokenizer.from_pretrained(retriever_path, local_files_only=True)
        model = AutoModel.from_pretrained(retriever_path, local_files_only=True)
        model.eval()
        print(f"   ✅ Retriever loaded")
        
     
        test_query = "triệu chứng viêm họng"
        inputs = tokenizer(test_query, return_tensors="pt", max_length=512, truncation=True, padding=True)
        
        with torch.no_grad():
            outputs = model(**inputs)
            embeddings = outputs.last_hidden_state.mean(dim=1)
        
        query_vector = embeddings.cpu().numpy().astype('float32')
        faiss_lib.normalize_L2(query_vector)
        print(f"   ✅ Query encoded: shape {query_vector.shape}")
        
       
        scores, indices = index.search(query_vector, 3)
        print(f"   ✅ Retrieval successful")
        
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx != -1 and idx < len(corpus):
                doc = corpus[idx]
                print(f"   📄 Doc {i+1}: [Score: {score:.3f}] {doc[:80]}...")
        
        print(f"   🎉 Complete RAG pipeline test SUCCESSFUL!")
        
    except Exception as e:
        print(f"   ❌ RAG pipeline test error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    debug_rag_components()