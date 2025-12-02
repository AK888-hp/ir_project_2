import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { API_BASE_URL } from '../config';

// --- Styled Components (Minimal set for visibility, based on static/style.css) ---
const Container = styled.div`
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1), 0 8px 16px rgba(0, 0, 0, 0.1);
  padding: 24px;
  
  width: 95%;          
  max-width: 1500px;   
  min-height: 70vh;    
  
  margin: 0 auto;
  text-align: center;
`;

const Title = styled.h1`
  color: #00A9A5;
  margin-bottom: 20px;
`;

const SearchArea = styled.div`
  display: flex;
  align-items: stretch;
  gap: 10px;
  margin-bottom: 20px;
  flex-direction: column; /* Stack input groups */
`;

const InputGroup = styled.div`
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
  border: 1px solid #eee;
  padding: 15px;
  border-radius: 6px;
`;

const InputText = styled.input`
  flex-grow: 1;
  font-size: 16px;
  border: 1px solid #ddd;
  padding: 10px;
  border-radius: 6px;
`;

const Button = styled.button`
  background-color: ${props => props.primary ? '#00A9A5' : '#4bc0c0'};
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  width: 150px;

  &:hover {
    background-color: ${props => props.primary ? '#008B85' : '#39a3a3'};
  }
  &:disabled {
    background-color: #ccc;
    cursor: not-allowed;
  }
`;

const Status = styled.div`
  margin-top: 20px;
  font-size: 18px;
  font-weight: 500;
  text-align: left;
  color: ${props => (props.isError ? 'red' : 'black')};
`;

const ResultsArea = styled.div`
  margin-top: 20px;
  padding-top: 10px;
  border-top: 1px solid #eee;
`;

const TextResultsBox = styled.div`
  margin-top: 10px;
  text-align: left;
  background-color: #f7f7f7;
  border: 1px solid #ddd;
  border-radius: 6px;
  padding: 15px;
  min-height: 50px;
  color: #1c1e21;
  & pre {
    color: #1c1e21;
    font-size: 14px; /* Optional: Make font a bit smaller for snippets */
  }
`;

const ImageResultsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
  text-align: left;
  margin-top: 10px;

  & img {
    width: 100%;
    height: auto;
    border-radius: 6px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  }
`;

// --- Unified Chat Component ---
const UnifiedChat = () => {
  const [textQuery, setTextQuery] = useState('');
  // File input is functionally disabled as all retrieval is now web-based
  const fileInputRef = useRef(null); 
  const [status, setStatus] = useState('Welcome! Enter a query for RAG or Web Image Search.');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // Helper function for NER color coding
  const getEntityColor = (group) => {
    switch(group) {
        case 'DISEASE': return '#ff6384';
        case 'SYMPTOM': return '#36a2eb';
        case 'DRUG': return '#ff9f40';
        case 'ANATOMY': return '#4bc0c0';
        case 'PROCEDURE': return '#9966ff';
        case 'ERROR': return '#dc3545';
        default: return '#cccccc';
    }
  };

  const handleTextRAG = async () => {
    if (!textQuery.trim()) {
      setStatus('Please enter a query for RAG/NLP search.', true);
      return;
    }

    setIsLoading(true);
    setResults(null);
    setStatus('Processing RAG and NLP via external APIs...');

    const formData = new FormData();
    formData.append('text_query', textQuery.trim()); 
    // Note: image_file is NOT appended, even if the user selects one

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || `HTTP error! Status: ${response.status}`);
      }

      setResults(data);
      setStatus(`RAG/NLP Search Complete. Found ${data.source_documents.length} web sources.`);

    } catch (error) {
      setStatus(`An error occurred during RAG/NLP Search: ${error.message}`, true);
      console.error('RAG Search Error:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleWebImageSearch = async () => {
    if (!textQuery.trim()) {
      setStatus('Please enter a query to search the web for an image.', true);
      return;
    }

    setIsLoading(true);
    setResults(null);
    setStatus('Searching web for image via external API...');

    const formData = new FormData();
    formData.append('query', textQuery.trim()); 

    try {
        const response = await fetch(`${API_BASE_URL}/search_image_web`, {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) { 
            throw new Error(data.message || `HTTP error! Status: ${response.status}`); 
        }
        
        if (data.results) { 
            setResults(data);
            setStatus(`Web Image Search Complete. Retrieved ${data.results.length} image(s).`);
        } else {
            setStatus('Web Image Search returned no results.', true);
        }

    } catch (error) {
        setStatus(`An error occurred during Web Image Search: ${error.message}`, true);
        console.error('Web Image Search Error:', error);
    } finally {
        setIsLoading(false);
    }
  };

  const handleTextChange = (e) => {
    setTextQuery(e.target.value);
  };
  
  const handleFileDrop = (e) => {
    // This function is included only to signal to the user that file search is disabled
    e.preventDefault();
    setStatus('Image similarity search is disabled. Please use the text input for web retrieval.', true);
    if(fileInputRef.current) fileInputRef.current.value = '';
  };


  const renderResults = () => {
    if (!results) return null;

    if (results.results) { // Image Results
      return (
        <ImageResultsGrid>
          {results.results.map((base64DataUrl, index) => (
            <img key={index} src={base64DataUrl} alt={`Result ${index + 1}`} />
          ))}
          <p style={{ gridColumn: '1 / -1', textAlign: 'center', fontSize: '14px', color: '#666' }}>
              {results.message || 'Image retrieved from conceptual Web Search API.'}
          </p>
        </ImageResultsGrid>
      );
    } 
    
    // RAG + NLP Results
    if (results.answer) { 
        return (
            <TextResultsBox>
                <h3>AI Generated Answer (Web RAG):</h3>
                <pre>{results.answer}</pre>
                
                {/* --- NLP ENTITY RESULTS --- */}
                {results.ner_results && results.ner_results.length > 0 && (
                    <details open style={{ marginTop: '25px', padding: '10px', border: '1px solid #00A9A5', borderRadius: '4px', backgroundColor: '#e6fffb' }}>
                        <summary style={{ fontWeight: 'bold', cursor: 'pointer', color: '#008B85' }}>
                            🏥 Extracted Medical Entities (NLP)
                        </summary>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '10px' }}>
                            {results.ner_results
                                .filter(entity => entity.entity_group && entity.word)
                                .map((entity, index) => (
                                <span 
                                    key={index} 
                                    title={`Confidence: ${entity.score.toFixed(4)}`}
                                    style={{
                                        backgroundColor: getEntityColor(entity.entity_group) + '33',
                                        color: getEntityColor(entity.entity_group),
                                        padding: '5px 10px',
                                        borderRadius: '20px',
                                        fontSize: '14px',
                                        fontWeight: '600',
                                        border: `1px solid ${getEntityColor(entity.entity_group)}`
                                    }}
                                >
                                    {entity.word} ({entity.entity_group})
                                </span>
                            ))}
                        </div>
                    </details>
                )}

                {/* Display Source Documents as Web Snippets */}
                {results.source_documents && results.source_documents.length > 0 && (
                    <details open style={{ marginTop: '15px', padding: '10px', border: '1px solid #ddd', borderRadius: '4px' }}>
                        <summary style={{ fontWeight: 'bold', cursor: 'pointer' }}>🌐 Web Snippets Used for Context ({results.source_documents.length})</summary>
                        {results.source_documents.map((doc, index) => (
                            <pre key={index} style={{ fontSize: '12px', margin: '5px 0' }}>
                                {`--- Web Snippet ${index + 1} ---\n${doc}`}
                            </pre>
                        ))}
                    </details>
                )}
            </TextResultsBox>
        );
    }

    return null;
  };

  return (
    <Container>
      <Title>Web-Based Multimodal Chatbot</Title>
      <p>Enter a query below, then choose whether to perform **RAG/NLP** or **Web Image Search**.</p>

      <SearchArea>
        {/* File Input is disabled to enforce Web-Based retrieval */}
        <input 
            type="file" 
            ref={fileInputRef} 
            disabled 
            style={{ width: '100%', marginBottom: '10px' }}
            title="Local file search is disabled in Web-Based mode"
            onDrop={handleFileDrop} 
            onClick={(e) => { e.preventDefault(); setStatus('Local file search is disabled. Use text input for web searches.', true); }}
        />
        <InputText
          type="text"
          placeholder="e.g., 'What are the symptoms of fever?' or 'Find a picture of the Eiffel Tower'"
          value={textQuery}
          onChange={handleTextChange}
          onKeyDown={(e) => e.key === 'Enter' && handleTextRAG()}
          disabled={isLoading}
        />
        
        <InputGroup>
            <Button primary onClick={handleTextRAG} disabled={isLoading || !textQuery.trim()}>
                {isLoading ? 'Processing RAG...' : 'Search RAG/NLP'}
            </Button>
            <Button onClick={handleWebImageSearch} disabled={isLoading || !textQuery.trim()}>
                {isLoading ? 'Searching Image...' : 'Search Web Image'}
            </Button>
        </InputGroup>
      </SearchArea>

      <Status isError={status.startsWith('An error')}>{status}</Status>
      <ResultsArea>
        {renderResults()}
      </ResultsArea>
    </Container>
  );
};

export default UnifiedChat;