import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import styled from 'styled-components';
import UnifiedChat from './components/UnifiedChat';

const AppContainer = styled.div`
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: #f0f2f5;
  min-height: 100vh;
  padding: 20px;
  /* --- FIX 1: Ensure the outer wrapper uses full width --- */
  width: 100%;
`;

const Nav = styled.nav`
  text-align: center;
  margin-bottom: 20px;
  background-color: #ffffff;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

function App() {
  return (
    <Router>
      <AppContainer>
        <Nav>
          <span style={{ fontSize: '18px', padding: '10px 15px', color: '#00A9A5', fontWeight: 'bold' }}>
            Web-Based Multimodal Chatbot
          </span>
        </Nav>
        <Routes>
          <Route path="/" element={<UnifiedChat />} />
        </Routes>
      </AppContainer>
    </Router>
  );
}

export default App;