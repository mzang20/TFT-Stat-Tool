import { useState } from 'react';
import TopTraits from './topTraits';
import TopItems from './topItems';

function App() {
  const [activeTab, setActiveTab] = useState('traits');
  const [gameName, setGameName] = useState('');
  const [tagLine, setTagLine] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [traitsData, setTraitsData] = useState(null);
  const [itemsData, setItemsData] = useState(null);

  const handleSearch = async () => {
    if (!gameName.trim() || !tagLine.trim()) {
      setError('Please enter both Game Name and Tag Line');
      return;
    }

    setLoading(true);
    setError('');
    setTraitsData(null);
    setItemsData(null);

    try {
      console.log('Making request with Riot ID:', `${gameName.trim()}#${tagLine.trim()}`);
      
      const baseUrl = 'https://tft-stat-tool.onrender.com';
      const params = `gameName=${encodeURIComponent(gameName.trim())}&tagLine=${encodeURIComponent(tagLine.trim())}`;
      
      // Fetch traits and items in parallel
      const [traitsResponse, itemsResponse] = await Promise.all([
        fetch(`${baseUrl}/analyze-traits-riot-id?${params}`, { method: 'GET' }),
        fetch(`${baseUrl}/analyze-items-riot-id?${params}`, { method: 'GET' })
      ]);

      console.log('Traits response status:', traitsResponse.status);
      console.log('Items response status:', itemsResponse.status);
      
      // Handle traits response
      if (traitsResponse.ok) {
        const traitsText = await traitsResponse.text();
        const traitsData = JSON.parse(traitsText);
        setTraitsData(traitsData);
        console.log('Traits data:', traitsData);
      } else {
        const traitsError = await traitsResponse.text();
        console.error('Traits error:', traitsError);
      }
      
      // Handle items response
      if (itemsResponse.ok) {
        const itemsText = await itemsResponse.text();
        const itemsData = JSON.parse(itemsText);
        setItemsData(itemsData);
        console.log('Items data:', itemsData);
      } else {
        const itemsError = await itemsResponse.text();
        console.error('Items error:', itemsError);
      }
      
      // If all failed, show error
      if (!traitsResponse.ok && !itemsResponse.ok) {
        throw new Error(`Analysis failed. Traits: ${traitsResponse.status}, Items: ${itemsResponse.status}`);
      }
      
      // Switch to the first successful tab to show results
      if (traitsResponse.ok) {
        setActiveTab('traits');
      } else if (itemsResponse.ok) {
        setActiveTab('items');
      }
      
    } catch (err) {
      console.error('Full error details:', err);
      setError(err.message || 'Analysis failed. Please check your Riot ID and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen bg-white text-gray-900 p-8">
      <h1 className="text-3xl font-bold text-center mb-4">TFT Stat Tool</h1>
       
      <div className="flex flex-col items-center mb-4">
        <div className="mb-4 text-center">
          <label className="block text-sm font-medium mb-2">Riot ID</label>
          <div className="flex items-center gap-2">
            <input 
              type="text" 
              className="input input-bordered input-sm w-40" 
              placeholder="Game Name"
              value={gameName}
              onChange={(e) => setGameName(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <span className="text-lg font-bold">#</span>
            <input 
              type="text" 
              className="input input-bordered input-sm w-20" 
              placeholder="Tag"
              value={tagLine}
              onChange={(e) => setTagLine(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Example: VIT k3soju#000
          </div>
        </div>
        
        <button 
          className={`btn btn-primary btn-sm ${loading ? 'loading' : ''}`}
          onClick={handleSearch}
          disabled={loading || !gameName.trim() || !tagLine.trim()}
        >
          {loading ? 'Analyzing...' : 'Search'}
        </button>
        
        {/* Error Display */}
        {error && (
          <div className="alert alert-error mt-4 max-w-md">
            <div>
              <svg xmlns="http://www.w3.org/2000/svg" className="stroke-current flex-shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}
      </div>
       
      <div role="tablist" className="tabs tabs-lifted justify-center">
        <button 
          role="tab" 
          className={`tab ${activeTab === 'traits' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('traits')}
          disabled={loading}
        >
          Traits
        </button>
        <button 
          role="tab" 
          className={`tab ${activeTab === 'items' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('items')}
          disabled={loading}
        >
          Items
        </button>
        <button 
          role="tab" 
          className={`tab ${activeTab === 'units' ? 'tab-active' : ''}`}
          onClick={() => setActiveTab('units')}
          disabled={loading}
        >
          Units
        </button>
      </div>

      {/* Tab Content */}
      <div className="mt-8 p-6 bg-gray-50 rounded-lg">
        {activeTab === 'traits' && (
          <TopTraits 
            data={traitsData} 
            loading={loading}
            hasSearched={!!traitsData || !!error}
          />
        )}
        {activeTab === 'items' && (
          <TopItems 
            data={itemsData} 
            loading={loading}
            hasSearched={!!itemsData || !!error}
          />
        )}
        {activeTab === 'units' && (
          <div>
            <h2 className="text-xl font-semibold mb-2">Units Content</h2>
            <p>This is the content for Units. Display unit information and stats here.</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;