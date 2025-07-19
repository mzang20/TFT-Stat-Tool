import { useState } from 'react';
import TopTraits from './topTraits';

function App() {
  const [activeTab, setActiveTab] = useState('augment');
  const [puid, setPuid] = useState('');

  return (
    <div className="min-h-screen bg-white text-gray-900 p-8">
      <h1 className="text-3xl font-bold text-center mb-4">TFT Stat Tool</h1>
       
      <div className="flex flex-col items-center mb-4">
        <div className="mb-4 text-center">
          <label className="block text-sm font-medium mb-2">PUUID</label>
          <input 
            type="text" 
            className="input input-bordered input-sm w-60" 
            placeholder="Enter PUUID"
            value={puid}
            onChange={(e) => setPuid(e.target.value)}
          />
        </div>
        <button className="btn btn-primary btn-sm">Search</button>
      </div>
       
      <div role="tablist" className="tabs tabs-lifted justify-center">
        <button 
          role="tab" 
          className={`tab ${activeTab === 'augment' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('augment')}
        >
          Augment
        </button>
        <button 
          role="tab" 
          className={`tab ${activeTab === 'units' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('units')}
        >
          Units
        </button>
        <button 
          role="tab" 
          className={`tab ${activeTab === 'traits' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('traits')}
        >
          Traits
        </button>
      </div>

      {/* Tab Content */}
      <div className="mt-8 p-6 bg-gray-50 rounded-lg">
        {activeTab === 'augment' && (
          <div>
            <h2 className="text-xl font-semibold mb-2">Augment Content</h2>
            <p>This is the content for Augment. You can display augment information here.</p>
          </div>
        )}
        {activeTab === 'units' && (
          <div>
            <h2 className="text-xl font-semibold mb-2">Units Content</h2>
            <p>This is the content for Units. Display unit information and stats here.</p>
          </div>
        )}
        {activeTab === 'traits' && (
            <TopTraits />
        )}
      </div>
    </div>
  );
}

export default App;
