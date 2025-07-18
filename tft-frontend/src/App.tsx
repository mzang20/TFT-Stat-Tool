function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-white p-8">
      <h1 className="text-3xl font-bold text-center mb-4">DaisyUI Test</h1>

      <div className="flex justify-center mb-4">
        <button className="btn btn-primary">Primary Button</button>
      </div>

      <div role="tablist" className="tabs tabs-lift justify-center">
        <a role="tab" className="tab tab-active">Tab 1</a>
        <a role="tab" className="tab">Tab 2</a>
        <a role="tab" className="tab">Tab 3</a>
      </div>
    </div>
  );
}

export default App;