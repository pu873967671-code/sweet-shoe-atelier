"""Camera-local semantic extraction for the retained open-toe worn painting.

Development candidate only. Coordinates describe satin, lining, support and metal;
source RGB is never used to decide whether a pixel is dyeable.
"""
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

# Closely sampled source contours. The narrow neutral piping belongs to the
# source painting and remains outside the full-colour inner satin regions.
REGIONS = {
 'ankle': [(498,379),(500,376),(512,382),(535,387),(564,391),(594,393),(625,394),(652,393),(673,390),(699,386),(722,380),(738,372),(741,379),(743,398),(733,403),(713,408),(686,412),(656,415),(625,416),(591,415),(561,412),(533,409),(510,404),(497,400)],
 'diagonal': [(466,500),(462,509),(458,521),(458,532),(462,542),(472,554),(486,567),(508,586),(532,605),(557,624),(581,645),(603,668),(622,690),(636,714),(644,737),(647,753),(662,735),(660,720),(654,701),(644,682),(628,662),(609,640),(586,619),(561,600),(538,581),(515,563),(494,546),(479,530),(472,518)],
 'counter': [(738,405),(743,414),(753,431),(765,448),(778,470),(791,494),(803,520),(812,546),(819,572),(819,596),(816,614),(809,632),(797,647),(777,661),(753,676),(729,689),(706,701),(711,687),(719,671),(726,650),(733,628),(741,601),(748,574),(753,547),(756,520),(757,495),(755,471),(750,447),(742,429)],
 'forefoot': [(269,817),(284,807),(301,796),(318,785),(333,778),(346,777),(363,780),(386,785),(409,793),(433,804),(455,817),(476,832),(495,849),(513,869),(530,891),(543,913),(551,931),(552,936),(535,943),(510,949),(482,953),(453,955),(437,952),(435,930),(430,911),(421,890),(409,871),(394,856),(376,843),(355,833),(334,825),(314,820),(295,817),(279,818)],
 # The visible satin-covered stem is independent of the warm heel cap.
 'heel': [(708,700),(728,683),(749,669),(771,654),(799,636),(792,650),(783,668),(776,687),(771,708),(768,734),(766,764),(765,797),(765,827),(766,848),(749,853),(747,849),(748,826),(749,797),(750,765),(750,736),(750,712),(748,695),(744,686),(737,682),(727,685)],
}
BUCKLE = [(669,389),(675,385),(701,383),(709,385),(712,391),(713,408),(708,416),(680,421),(672,418),(668,413)]
# Immutable lining/footbed/outsole areas are shoe, but never dye.
FIXED = [
 # Complete counter silhouette, including its cream outer piping. Satin dye
 # uses the inset REGIONS.counter; extracting this rim as skin lets socks
 # texture the outside of the shoe and gives the ankle a false wide edge.
 [(738,400),(745,400),(750,410),(755,420),(762,430),
  (769,440),(776,450),(782,460),(788,470),(794,480),
  (799,490),(804,500),(808,510),(812,520),(816,530),
  (819,540),(821,550),(824,570),(824,580),(823,590),
  (821,600),(819,610),(815,620),(810,630),(802,640),
  (790,650),(777,661),(753,676),(729,689),(706,701),
  (711,687),(719,671),(726,650),(733,628),(741,601),
  (748,574),(753,547),(756,520),(757,495),(755,471),
  (750,447),(742,429)],
 # Preserve the cream footbed below the big toe through x248. The remaining
 # contact edge follows each original toe lobe, including its warm underside
 # shading; that shading is skin, so opaque socks must cover it completely.
 [(168,924),(172,912),(184,903),(193,898),(199,905),(214,912),(232,917),(248,917),(255,923),(260,926),(270,928),(280,929),(284,929),(290,932),(300,934),(310,935),(320,934),(329,931),(333,931),(340,935),(350,937),(360,937),(370,934),(378,932),(381,932),(390,937),(400,937),(410,935),(420,933),(430,933),(435,930),(443,946),(530,947),(542,950),(533,959),(507,965),(470,968),(425,968),(375,968),(323,967),(274,964),(226,959),(192,952),(170,943)],
 [(531,884),(543,871),(555,848),(568,820),(583,788),(601,755),(620,721),(639,692),(660,665),(683,643),(707,626),(732,614),(730,633),(710,653),(690,677),(672,706),(653,737),(634,773),(616,812),(600,849),(585,888),(570,919),(555,941),(535,952),(526,944),(527,925)],
 [(706,700),(726,685),(745,682),(755,692),(757,715),(757,756),(760,801),(762,848),(767,855),(765,872),(747,878),(727,872),(727,853),(729,820),(729,779),(728,742),(725,718),(718,703)],
 # The cream inner sidewall is a broad continuous shoe face, separate from
 # the narrow warm footbed above it. Follow its full exterior arch rather
 # than the footbed's inner highlight: otherwise socks paint over the cream
 # triangle behind the diagonal band (notably source pixel 690,703).
 # This only adds fixed shell/occlusion, never upper dye or anatomy shaping.
 [(732,614),(707,626),(683,643),(660,665),(639,692),
  (620,721),(601,755),(583,788),(568,820),(555,848),
  (543,871),(531,884),(527,925),(526,944),(535,952),
  (543,950),(565,940),(576,930),(584,920),(590,910),
  (595,900),(599,890),(603,880),(607,870),(611,860),
  (615,850),(619,840),(623,830),(627,820),(631,810),
  (636,800),(641,790),(647,780),(653,770),(659,760),
  (665,750),(673,740),(681,730),(690,720),(701,710),
  (714,700),(728,690),(746,678),(754,657),
  (745,632)],
]

def _mask(size, polygons):
    """Supersampled contours retain smooth fractional coverage at native size."""
    scale=4
    im=Image.new('L',(size[0]*scale,size[1]*scale))
    draw=ImageDraw.Draw(im)
    for poly in polygons:
        draw.polygon([(round(x*scale),round(y*scale)) for x,y in poly],fill=255)
    return np.asarray(im.resize(size,Image.Resampling.LANCZOS),dtype=np.float64)/255

def semantic_fitting(a):
    """Return shell alpha, upper alpha, and authored semantic metadata.

    Input is normalized 1024-square RGBA source; alpha outputs are float 0..255.
    The source alpha clips exterior edges exactly. No skin RGB classification.
    """
    if a.shape != (1024,1024,4):
        raise ValueError('The fitting semantic masks require the fixed 1024-square camera')
    size=(1024,1024)
    satin=_mask(size,list(REGIONS.values()))
    metal=_mask(size,[BUCKLE])
    fixed=_mask(size,FIXED)
    upper=a[:,:,3].astype(float)*satin*(1-metal)
    # Include the original narrow stitched piping in shoe occlusion without
    # adding it to the dye region; socks must remain behind this edge.
    piping=np.asarray(Image.fromarray((satin*255).astype('uint8')).filter(ImageFilter.MaxFilter(7)),dtype=float)/255
    shell=a[:,:,3].astype(float)*np.maximum.reduce([piping,fixed,metal])
    return shell,upper,{'method':'authored-semantic-polygons-v3-toe-contact','dyeRegions':list(REGIONS),'excluded':['skin','toes','cream footbed','cream inner sidewall','warm lining','outsole','champagne buckle'],'acceptance':'development-only; complete rendered acceptance still required'}

if __name__ == '__main__':
    from pathlib import Path
    root=Path(__file__).resolve().parent/'sandal-source'
    a=np.array(Image.open(root/'fitting-normalized.png').convert('RGBA'))
    shell,upper,metadata=semantic_fitting(a)
    Image.fromarray(upper.astype('uint8')).save(root/'fitting-semantic-upper.png')
    Image.fromarray(shell.astype('uint8')).save(root/'fitting-semantic-shell.png')
    sheet=Image.new('RGB',(2048,1024),'#28444b')
    for i,tint in enumerate([(244,123,164),(42,51,69)]):
        rgb=a[:,:,:3].astype(float); strength=upper/255
        colour=np.array(tint)*np.clip(rgb.mean(axis=2)/235,.3,1.2)[:,:,None]
        rgb=rgb*(1-strength[:,:,None])+colour*strength[:,:,None]
        im=Image.fromarray(np.dstack([rgb.clip(0,255).astype('uint8'),a[:,:,3]]))
        sheet.paste(im,(i*1024,0),im)
    sheet.save(root/'fitting-semantic-review.jpg',quality=96)
    import json
    (root/'fitting-semantic-metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
