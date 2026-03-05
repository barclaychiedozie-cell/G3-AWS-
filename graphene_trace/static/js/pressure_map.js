(function(){
  var heatmap;

  function init(){
    var container = document.getElementById("heatmapContainer");
    heatmap = h337.create({ container: container, radius: 20, maxOpacity: 0.9, blur: 0.85 });
  }

  function gridToPoints(cells){
    if(!cells || !cells.length) return [];
    var maxR=0,maxC=0;
    cells.forEach(function(p){ maxR=Math.max(maxR,p.r); maxC=Math.max(maxC,p.c); });
    var rows=maxR+1, cols=maxC+1;

    var container = document.getElementById("heatmapContainer");
    var w = container.offsetWidth, h = container.offsetHeight;
    var cellW = w/cols, cellH = h/rows;

    return cells.map(function(p){
      return {
        x: Math.floor((p.c+0.5)*cellW),
        y: Math.floor((p.r+0.5)*cellH),
        value: Number(p.value)||0
      };
    });
  }

  function render(data){
    var points = gridToPoints(data.cells);
    var maxVal = points.reduce(function(m,p){return Math.max(m,p.value)}, 0);
    heatmap.setData({ max: Math.max(100, Math.ceil(maxVal)), min: 0, data: points });

    var el = document.getElementById("last-update");
    if(el) el.textContent = data.timestamp ? new Date(data.timestamp).toLocaleString() : "—";
  }

  function tick(){
    fetch(window.LIVE_GRID_URL, {credentials:"same-origin"})
      .then(r => r.json())
      .then(render)
      .catch(console.warn);
  }

  window.addEventListener("load", function(){
    init();
    tick();
    setInterval(tick, 2000);
  });
})();
// inside updateHeatmap(data) / render(data)
var sug = document.getElementById("reposition-suggestion");
if (sug) {
  if (data.reposition && data.reposition.reason) {
    sug.style.display = "block";
    sug.textContent = data.reposition.reason;
  } else {
    sug.style.display = "none";
    sug.textContent = "";
  }
}