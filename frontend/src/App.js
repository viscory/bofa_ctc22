import { BrowserRouter, Routes, Route } from 'react-router-dom';
import './App.css';
import Home from './Home';

import React from 'react';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <BrowserRouter>
          <Routes>
            <Route exact path="/" element= {<Home/>}>
            </Route>
          </Routes>
        </BrowserRouter>
      </header>
    </div>
  );
}

export default App;
