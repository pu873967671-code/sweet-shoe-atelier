'use strict';
// Node compatibility entry for QA; the browser loads the plain scripts in index.html.
require('./js/data.js');
require('./js/merge-core.js');
require('./js/merge-storage.js');
require('./js/atelier-progression.js');
require('./js/studio-core.js');
require('./js/accessory-renderer.js');
require('./js/merge-orders.js');
require('./js/merge-rewards.js');
require('./js/merge-bubbles.js');
require('./js/boutique.js');
require('./js/showcase.js');
require('./js/save.js');
require('./js/introduction.js');
require('./js/fabric-regions.js');
require('./js/shoe-renderer.js');
require('./js/worn-body-fidelity.js');
module.exports=globalThis.SweetShoe;
