import React, { useState, useRef } from 'react';
import styled from 'styled-components';
import { API_BASE_URL } from '../config';

// --- Styled Components (Minimal set for visibility, based on static/style.css) ---
const Container = styled.div`
  background-color: #ffffff;
  border-radius: 0;   /* flush with edges; optional */
  box-shadow: none;   /* optional: remove shadow if you want flat full-width */
  padding: 24px;

  width: 100vw;       /* full viewport width */
  max-width: 100vw;
  min-height: 100vh;  /* full screen height */

  margin: 0;
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
  background-color: ${props => (props.primary ? '#00A9A5' : '#4bc0c0')};
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 16px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background-color 0.2s;
  width: 150px;

  &:hover {
    background-color: ${props => (props.primary ? '#008B85' : '#39a3a3')};
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
  overflow-x: auto;      /* safety: horizontal scroll if *really* needed */
  max-width: 100%;

  & pre {
    color: #1c1e21;
    font-size: 14px;
    white-space: pre-wrap;   /* allow wrapping but keep line breaks */
    word-break: break-word;  /* break long continuous strings */
    overflow-wrap: anywhere; /* extra safety for long URLs etc. */
    margin: 0;               /* optional: remove default pre margin */
    max-width: 100%;
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
  const fileInputRef = useRef(null);

  const [status, setStatus] = useState('Welcome! Type a question and/or upload an image.');
  const [results, setResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadedImagePreview, setUploadedImagePreview] = useState(null);

  const getEntityColor = (group) => {
    switch (group) {
      case 'DISEASE': return '#ff6384';
      case 'SYMPTOM': return '#36a2eb';
      case 'DRUG': return '#ff9f40';
      case 'ANATOMY': return '#4bc0c0';
      case 'PROCEDURE': return '#9966ff';
      case 'ERROR': return '#dc3545';
      default: return '#cccccc';
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file || null);
    setUploadedImagePreview(null);
    if (file) {
      setStatus(`Selected file: ${file.name}`);
    }
  };

  const handleTextChange = (e) => {
    setTextQuery(e.target.value);
  };

  // --- Single unified multimodal handler ---
  const handleMultimodalChat = async () => {
  if (!textQuery.trim() && !selectedFile) {
    setStatus('Please enter a question or upload an image.');
    return;
  }

  setIsLoading(true);
  setResults(null);
  setUploadedImagePreview(null);
  setStatus('Sending multimodal query to chatbot...');

  const formData = new FormData();
  if (textQuery.trim()) formData.append('text_query', textQuery.trim());
  formData.append('mode', 'auto');
  if (selectedFile) formData.append('file', selectedFile);

  try {
    const response = await fetch(`${API_BASE_URL}/multimodal_chat`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || data.message || `HTTP error! Status: ${response.status}`);
    }

    setResults(data);
    setStatus(data.message || `Mode: ${data.mode}`);

    if (data.images && data.images.length > 0 && data.mode && data.mode.startsWith('image_')) {
      setUploadedImagePreview(data.images[0]);
    }

    // 🔹 Clear query & file after a successful run
    setTextQuery('');
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';  // reset the <input type="file">
    }
  } catch (err) {
    setStatus(`An error occurred in multimodal chat: ${err.message}`);
    console.error('Multimodal Chat Error:', err);
  } finally {
    setIsLoading(false);
  }
};

  const renderResults = () => {
    if (!results) return null;

    const hasImages = Array.isArray(results.images) && results.images.length > 0;
    const hasAnswer = !!results.answer;

    return (
      <>
        {/* Text answer (RAG / explanation / caption) */}
        {hasAnswer && (
          <TextResultsBox>
            <h3>AI Generated Answer:</h3>
            <pre>{results.answer}</pre>

            {/* NLP entities */}
            {results.ner_results && results.ner_results.length > 0 && (
              <details
                open
                style={{
                  marginTop: '25px',
                  padding: '10px',
                  border: '1px solid #00A9A5',
                  borderRadius: '4px',
                  backgroundColor: '#e6fffb',
                }}
              >
                <summary
                  style={{
                    fontWeight: 'bold',
                    cursor: 'pointer',
                    color: '#008B85',
                  }}
                >
                  🏥 Extracted Medical Entities (NLP)
                </summary>
                <div
                  style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    gap: '8px',
                    marginTop: '10px',
                  }}
                >
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
                          border: `1px solid ${getEntityColor(entity.entity_group)}`,
                        }}
                      >
                        {entity.word} ({entity.entity_group})
                      </span>
                    ))}
                </div>
              </details>
            )}

            {/* Web snippets */}
            {results.source_documents && results.source_documents.length > 0 && (
              <details
                open
                style={{
                  marginTop: '15px',
                  padding: '10px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                }}
              >
                <summary style={{ fontWeight: 'bold', cursor: 'pointer' }}>
                  🌐 Web Snippets Used for Context ({results.source_documents.length})
                </summary>
                {results.source_documents.map((doc, index) => (
                  <pre key={index} style={{ fontSize: '12px', margin: '5px 0' }}>
                    {`--- Web Snippet ${index + 1} ---\n${doc}`}
                  </pre>
                ))}
              </details>
            )}
          </TextResultsBox>
        )}

        {/* Images (text→image or image→image) */}
        {hasImages && (
  <ImageResultsGrid>
    {results.images
      .filter(Boolean)                // remove null/undefined/empty strings
      .slice(0, 24)                   // show only first 24, to avoid crazy long pages
      .map((src, index) => (
        <img
          key={index}
          src={src}
          alt={`Result ${index + 1}`}
          loading="lazy"
          onError={(e) => {
            // Hide broken / blocked images so you don't see empty tiles
            e.currentTarget.style.display = "none";
          }}
        />
      ))}
  </ImageResultsGrid>
)}

      </>
    );
  };

  const isError = status.toLowerCase().includes('error');

  return (
    <Container>
      <Title>Medical Chatbot — MedAI Assistant</Title>
      <p>
        Retrive medical related texts and images from Web
      </p>

      <SearchArea>
        <input
          type="file"
          ref={fileInputRef}
          accept="image/*"
          style={{ width: '100%', marginBottom: '10px' }}
          onChange={handleFileChange}
        />

        <InputText
          type="text"
          placeholder="Ask anything... e.g., 'What are the symptoms of fever?' or 'Show me an image of pneumonia x-ray'"
          value={textQuery}
          onChange={handleTextChange}
          onKeyDown={(e) => e.key === 'Enter' && handleMultimodalChat()}
          disabled={isLoading}
        />

        <InputGroup>
          <Button primary onClick={handleMultimodalChat} disabled={isLoading}>
            {isLoading ? 'Thinking...' : 'Ask Chatbot'}
          </Button>
        </InputGroup>
      </SearchArea>

      <Status isError={isError}>{status}</Status>

      <ResultsArea>
        {/* Uploaded image preview (for image modes) */}
        {uploadedImagePreview && (
          <div style={{ marginBottom: '20px', textAlign: 'left' }}>
            <h3>Uploaded Image Preview:</h3>
            <img
              src={uploadedImagePreview}
              alt="Uploaded preview"
              style={{ maxWidth: '250px', borderRadius: '8px', marginTop: '10px' }}
            />
          </div>
        )}

        {renderResults()}
      </ResultsArea>
    </Container>
  );
};

export default UnifiedChat;
