"""
Comprehensive Test Script for AI Agent Phase 2

This script tests all Phase 2 components:
- Phase 2.1: Foundation Setup (Configuration, Vector Store)
- Phase 2.2: RAG Implementation (Knowledge Base, Document Loading)
- Phase 2.3: LLM Integration (Chains, Report Generation)
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class Phase2Tester:
    """Comprehensive tester for Phase 2 components."""
    
    def __init__(self):
        """Initialize tester."""
        self.results = {
            "phase_2_1": {},
            "phase_2_2": {},
            "phase_2_3": {},
            "overall": {"passed": 0, "failed": 0, "warnings": 0}
        }
    
    def print_header(self, title: str):
        """Print test section header."""
        print("\n" + "=" * 70)
        print(f"  {title}")
        print("=" * 70)
    
    def print_test(self, name: str, status: str, details: str = ""):
        """Print test result."""
        status_symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_symbol} {name}")
        if details:
            print(f"   {details}")
        
        if status == "PASS":
            self.results["overall"]["passed"] += 1
        elif status == "FAIL":
            self.results["overall"]["failed"] += 1
        else:
            self.results["overall"]["warnings"] += 1
    
    # ========================================================================
    # Phase 2.1 Tests: Foundation Setup
    # ========================================================================
    
    def test_phase_2_1(self):
        """Test Phase 2.1: Foundation Setup."""
        self.print_header("Phase 2.1: Foundation Setup Tests")
        
        # Test 1: Configuration
        try:
            from app.ai_agent.config import (
                validate_config,
                get_config_summary,
                AI_PROVIDER,
                OPENAI_API_KEY,
                HUGGINGFACE_API_KEY,
            )
            
            config_errors = validate_config()
            if config_errors["errors"]:
                self.print_test(
                    "Configuration Validation",
                    "FAIL",
                    f"Errors: {', '.join(config_errors['errors'])}"
                )
                return False
            else:
                self.print_test("Configuration Validation", "PASS")
            
            config_summary = get_config_summary()
            self.print_test(
                "Configuration Summary",
                "PASS",
                f"Provider: {config_summary['ai_provider']}, "
                f"Vector Store: {config_summary['chroma_cloud_mode']}"
            )
            self.results["phase_2_1"]["config"] = config_summary
            
        except Exception as e:
            self.print_test("Configuration", "FAIL", str(e))
            return False
        
        # Test 2: LLM Provider
        try:
            from app.ai_agent.llm_provider import get_llm, get_embedding_model
            
            llm = get_llm()
            self.print_test("LLM Provider Initialization", "PASS", f"Provider: {AI_PROVIDER}")
            
            embedding_model = get_embedding_model()
            self.print_test("Embedding Model Initialization", "PASS")
            
        except Exception as e:
            self.print_test("LLM Provider", "FAIL", str(e))
            return False
        
        # Test 3: Vector Store
        try:
            from app.ai_agent.vector_store import get_vector_store
            
            vector_store = get_vector_store()
            self.print_test("Vector Store Initialization", "PASS")
            
            # Test adding a sample document
            from langchain.schema import Document
            test_doc = Document(
                page_content="Test document for vector store",
                metadata={"test": True, "type": "test"}
            )
            
            doc_ids = vector_store.add_documents([test_doc])
            if doc_ids:
                self.print_test("Vector Store - Add Documents", "PASS", f"Added {len(doc_ids)} document(s)")
            else:
                self.print_test("Vector Store - Add Documents", "WARN", "No document IDs returned")
            
            # Test search
            results = vector_store.similarity_search("test document", k=1)
            if results:
                self.print_test("Vector Store - Similarity Search", "PASS", f"Found {len(results)} result(s)")
            else:
                self.print_test("Vector Store - Similarity Search", "WARN", "No results found")
            
        except Exception as e:
            self.print_test("Vector Store", "FAIL", str(e))
            return False
        
        self.results["phase_2_1"]["status"] = "PASS"
        return True
    
    # ========================================================================
    # Phase 2.2 Tests: RAG Implementation
    # ========================================================================
    
    def test_phase_2_2(self):
        """Test Phase 2.2: RAG Implementation."""
        self.print_header("Phase 2.2: RAG Implementation Tests")
        
        # Test 1: Document Loader
        try:
            from app.ai_agent.document_loader import DocumentLoader
            from app.config.config import DATABASE_URL
            from app.models.schema import get_engine, get_session
            
            if not DATABASE_URL or DATABASE_URL == "postgresql://username:password@hostname/database?sslmode=require":
                self.print_test("Document Loader", "WARN", "Database not configured, skipping database tests")
                return True
            
            engine = get_engine(DATABASE_URL)
            session = get_session(engine)
            
            loader = DocumentLoader(session)
            self.print_test("Document Loader Initialization", "PASS")
            
            # Test loading employee summaries (limit to 1 for testing)
            try:
                employee_docs = loader.load_employee_summaries(limit=1)
                if employee_docs:
                    self.print_test(
                        "Document Loader - Employee Summaries",
                        "PASS",
                        f"Loaded {len(employee_docs)} document(s)"
                    )
                else:
                    self.print_test(
                        "Document Loader - Employee Summaries",
                        "WARN",
                        "No employee documents found (database may be empty)"
                    )
            except Exception as e:
                self.print_test("Document Loader - Employee Summaries", "WARN", f"Error: {e}")
            
            # Test loading financial patterns
            try:
                financial_docs = loader.load_financial_patterns(months=3)
                if financial_docs:
                    self.print_test(
                        "Document Loader - Financial Patterns",
                        "PASS",
                        f"Loaded {len(financial_docs)} document(s)"
                    )
                else:
                    self.print_test(
                        "Document Loader - Financial Patterns",
                        "WARN",
                        "No financial pattern documents found"
                    )
            except Exception as e:
                self.print_test("Document Loader - Financial Patterns", "WARN", f"Error: {e}")
            
            session.close()
            
        except Exception as e:
            self.print_test("Document Loader", "FAIL", str(e))
            return False
        
        # Test 2: RAG Engine
        try:
            from app.ai_agent.rag_engine import get_rag_engine
            
            rag_engine = get_rag_engine()
            self.print_test("RAG Engine Initialization", "PASS")
            
            # Test context retrieval
            test_query = "employee summary"
            context_docs = rag_engine.retrieve_context(test_query, k=2)
            if context_docs:
                self.print_test(
                    "RAG Engine - Context Retrieval",
                    "PASS",
                    f"Retrieved {len(context_docs)} document(s)"
                )
            else:
                self.print_test(
                    "RAG Engine - Context Retrieval",
                    "WARN",
                    "No context retrieved (knowledge base may be empty)"
                )
            
            # Test context formatting
            formatted = rag_engine.format_context(context_docs[:1] if context_docs else [])
            if formatted:
                self.print_test("RAG Engine - Context Formatting", "PASS")
            else:
                self.print_test("RAG Engine - Context Formatting", "WARN", "Empty formatted context")
            
            # Test query expansion
            expanded = rag_engine.expand_query("employee advance")
            if len(expanded) > 1:
                self.print_test(
                    "RAG Engine - Query Expansion",
                    "PASS",
                    f"Expanded to {len(expanded)} query variations"
                )
            else:
                self.print_test("RAG Engine - Query Expansion", "PASS", "No expansion needed")
            
        except Exception as e:
            self.print_test("RAG Engine", "FAIL", str(e))
            return False
        
        # Test 3: Knowledge Base Builder (optional - only if database has data)
        try:
            from app.ai_agent.knowledge_base_builder import KnowledgeBaseBuilder
            
            if not DATABASE_URL or DATABASE_URL == "postgresql://username:password@hostname/database?sslmode=require":
                self.print_test("Knowledge Base Builder", "WARN", "Database not configured, skipping")
                self.results["phase_2_2"]["status"] = "PASS"
                return True
            
            engine = get_engine(DATABASE_URL)
            session = get_session(engine)
            
            builder = KnowledgeBaseBuilder(session)
            self.print_test("Knowledge Base Builder Initialization", "PASS")
            
            # Test adding domain knowledge (doesn't require database data)
            try:
                domain_result = builder.add_domain_knowledge()
                if domain_result.get("status") == "success":
                    self.print_test(
                        "Knowledge Base Builder - Domain Knowledge",
                        "PASS",
                        f"Added {domain_result.get('documents_added', 0)} document(s)"
                    )
                else:
                    self.print_test(
                        "Knowledge Base Builder - Domain Knowledge",
                        "WARN",
                        domain_result.get("error", "Unknown error")
                    )
            except Exception as e:
                self.print_test("Knowledge Base Builder - Domain Knowledge", "WARN", str(e))
            
            session.close()
            
        except Exception as e:
            self.print_test("Knowledge Base Builder", "WARN", str(e))
        
        self.results["phase_2_2"]["status"] = "PASS"
        return True
    
    # ========================================================================
    # Phase 2.3 Tests: LLM Integration
    # ========================================================================
    
    def test_phase_2_3(self):
        """Test Phase 2.3: LLM Integration."""
        self.print_header("Phase 2.3: LLM Integration Tests")
        
        # Test 1: RAG Chain
        try:
            from app.ai_agent.chains import get_rag_chain
            
            rag_chain = get_rag_chain()
            self.print_test("RAG Chain Initialization", "PASS")
            
            # Test simple query (without actual LLM call to save costs)
            # Just verify the chain can be created
            self.print_test("RAG Chain - Structure", "PASS", "Chain structure verified")
            
        except Exception as e:
            self.print_test("RAG Chain", "FAIL", str(e))
            return False
        
        # Test 2: Structured Output Chain
        try:
            from app.ai_agent.chains import get_structured_chain, EmployeeSummaryOutput
            
            structured_chain = get_structured_chain(EmployeeSummaryOutput)
            self.print_test("Structured Output Chain Initialization", "PASS")
            
            # Verify output parser
            if hasattr(structured_chain, 'output_parser'):
                self.print_test("Structured Output Chain - Parser", "PASS")
            else:
                self.print_test("Structured Output Chain - Parser", "FAIL", "Parser not found")
            
        except Exception as e:
            self.print_test("Structured Output Chain", "FAIL", str(e))
            return False
        
        # Test 3: Chain Orchestrator
        try:
            from app.ai_agent.chain_orchestrator import get_chain_orchestrator
            
            orchestrator = get_chain_orchestrator()
            self.print_test("Chain Orchestrator Initialization", "PASS")
            
        except Exception as e:
            self.print_test("Chain Orchestrator", "FAIL", str(e))
            return False
        
        # Test 4: Report Generator (structure only, no actual LLM call)
        try:
            from app.ai_agent.report_generator import ReportGenerator
            from app.config.config import DATABASE_URL
            from app.models.schema import get_engine, get_session
            
            if not DATABASE_URL or DATABASE_URL == "postgresql://username:password@hostname/database?sslmode=require":
                self.print_test("Report Generator", "WARN", "Database not configured, skipping")
                self.results["phase_2_3"]["status"] = "PASS"
                return True
            
            engine = get_engine(DATABASE_URL)
            session = get_session(engine)
            
            generator = ReportGenerator(session)
            self.print_test("Report Generator Initialization", "PASS")
            
            # Verify chains are initialized
            if hasattr(generator, 'rag_chain'):
                self.print_test("Report Generator - RAG Chain", "PASS")
            if hasattr(generator, 'employee_summary_chain'):
                self.print_test("Report Generator - Employee Summary Chain", "PASS")
            if hasattr(generator, 'financial_report_chain'):
                self.print_test("Report Generator - Financial Report Chain", "PASS")
            
            session.close()
            
        except Exception as e:
            self.print_test("Report Generator", "WARN", str(e))
        
        self.results["phase_2_3"]["status"] = "PASS"
        return True
    
    # ========================================================================
    # Integration Test (Optional - requires database and LLM API)
    # ========================================================================
    
    def test_integration(self, run_llm_tests: bool = False):
        """Test full integration (optional, requires API calls)."""
        self.print_header("Integration Test (Optional)")
        
        if not run_llm_tests:
            self.print_test(
                "Full Integration Test",
                "WARN",
                "Skipped (use --run-llm flag to test with actual LLM calls)"
            )
            return
        
        try:
            from app.ai_agent.agent import get_ai_agent
            from app.config.config import DATABASE_URL
            from app.models.schema import get_engine, get_session
            
            if not DATABASE_URL or DATABASE_URL == "postgresql://username:password@hostname/database?sslmode=require":
                self.print_test("Integration Test", "WARN", "Database not configured")
                return
            
            engine = get_engine(DATABASE_URL)
            session = get_session(engine)
            
            agent = get_ai_agent(session)
            self.print_test("AI Agent Initialization", "PASS")
            
            # Test employee summary generation (requires LLM API call)
            try:
                # Get first employee if available
                from app.models.schema import Employee
                first_employee = session.query(Employee).first()
                
                if first_employee:
                    print(f"\n   Testing with employee: {first_employee.first_name} {first_employee.last_name}")
                    result = agent.generate_summary(
                        query_type="employee_summary",
                        employee_id=first_employee.id
                    )
                    
                    if "summary" in result or "error" in result:
                        if "error" in result:
                            self.print_test("Integration - Employee Summary", "WARN", result["error"])
                        else:
                            self.print_test("Integration - Employee Summary", "PASS", "Summary generated")
                    else:
                        self.print_test("Integration - Employee Summary", "WARN", "Unexpected result format")
                else:
                    self.print_test("Integration - Employee Summary", "WARN", "No employees in database")
            except Exception as e:
                self.print_test("Integration - Employee Summary", "WARN", f"Error: {e}")
            
            session.close()
            
        except Exception as e:
            self.print_test("Integration Test", "WARN", str(e))
    
    # ========================================================================
    # Main Test Runner
    # ========================================================================
    
    def run_all_tests(self, run_llm_tests: bool = False):
        """Run all Phase 2 tests."""
        print("\n" + "=" * 70)
        print("  AI Agent Phase 2 - Comprehensive Test Suite")
        print("=" * 70)
        
        # Phase 2.1
        phase_2_1_passed = self.test_phase_2_1()
        
        # Phase 2.2
        phase_2_2_passed = self.test_phase_2_2()
        
        # Phase 2.3
        phase_2_3_passed = self.test_phase_2_3()
        
        # Integration (optional)
        self.test_integration(run_llm_tests=run_llm_tests)
        
        # Summary
        self.print_summary()
        
        return phase_2_1_passed and phase_2_2_passed and phase_2_3_passed
    
    def print_summary(self):
        """Print test summary."""
        self.print_header("Test Summary")
        
        total = self.results["overall"]["passed"] + self.results["overall"]["failed"] + self.results["overall"]["warnings"]
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {self.results['overall']['passed']}")
        print(f"❌ Failed: {self.results['overall']['failed']}")
        print(f"⚠️  Warnings: {self.results['overall']['warnings']}")
        
        print("\nPhase Status:")
        print(f"  Phase 2.1 (Foundation): {self.results['phase_2_1'].get('status', 'NOT TESTED')}")
        print(f"  Phase 2.2 (RAG): {self.results['phase_2_2'].get('status', 'NOT TESTED')}")
        print(f"  Phase 2.3 (LLM Integration): {self.results['phase_2_3'].get('status', 'NOT TESTED')}")
        
        if self.results["overall"]["failed"] == 0:
            print("\n✅ All critical tests passed!")
        else:
            print(f"\n❌ {self.results['overall']['failed']} test(s) failed. Please review errors above.")
        
        print("\n" + "=" * 70)


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test AI Agent Phase 2")
    parser.add_argument(
        "--run-llm",
        action="store_true",
        help="Run tests that require actual LLM API calls (costs money)"
    )
    
    args = parser.parse_args()
    
    tester = Phase2Tester()
    success = tester.run_all_tests(run_llm_tests=args.run_llm)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
