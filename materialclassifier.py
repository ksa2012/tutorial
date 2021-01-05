import logging
import re

log = logging.getLogger(__name__)
g_material_layers = {}

IGNORE_CATS = ['Beauty']
IGNORE_SUBCATS = ['Activewear Accessories | Activewear Equipments']
AVAILABLE_CATS = ['Shoes', 'Eyewear', 'Accessories', 'Bags', 'Jewellery']

def getMaterial(category, subcategories, Text, test = None):
    try:
        Text = Text.lower()
        Text = re.sub(r"[./<>,]+"," . ",Text)
        s_key = ''
        materials = []

        if test:
            SetMaterials(Text, s_key, materials, category, subcategories, test)

        if category in IGNORE_CATS:
            pass
        elif any(subcat in IGNORE_SUBCATS for subcat in subcategories):
            pass
        elif category in AVAILABLE_CATS:
            s_key = category
            if category == 'Shoes':
                #print('Material Shoes', Text)
                Text = shoes_unwanted_words(Text)
            SetMaterials(Text, s_key, materials, category, subcategories)
        elif category not in AVAILABLE_CATS:
            s_key = 'Clothing'
            SetMaterials(Text, s_key, materials, category, subcategories)

        if not materials:
            materials.append('*')

        materials = list(set(materials))
        # print('Materials : {}, Category : {}, Style : {}'.format(materials, category, subcategories))
        return {'materials': materials}
    except:
        log.error( 'algo: Error - material: {}'.format(Text), exc_info=1)
        return {'materials': ['*']}


def shoes_unwanted_words(Text):

    Text= Text.replace('</li>', '.')
    Text= Text.replace('\n', '.')

    unwanted_words = [
        'styled it with', 'other details include', 'with your fav', 'rubber lace',
        'rubberised eyelet', 'rubberized eyelet', 'rubberised insert', 'rubberized insert', 'rubber insert',
        'trimmed canvas', 'rubberised trim', 'rubberized trim'
    ]

    unwanted_combi_words = [
        ['rubber', 'sole'], ['rubber', ' logo'], ['rubber', 'heel counter'], ['rubberised', ' lace'],
        ['rubberized', ' lace'], ['sheepskin', 'lined'], ['sheepskin', 'lining'], ['cotton', 'lining'],
        ['cotton', 'lined'], ['fleece', 'lining'], ['fleece', 'lined'], ['microfibre', 'lined'], ['micro fibre', 'lined'], ['microfiber', 'lined'], ['micro fiber', 'lined'],
        ['microfibre', 'lining'],['micro fibre', 'lining'], ['microfiber', 'lining'], ['micro fiber', 'lining'], ['microfibre', 'heel counter'],['micro fibre', 'heel counter'], ['neoprene', 'facing'],
        ['microfiber', 'heel counter'],['micro fiber', 'heel counter'], ['shearling', 'lining'], ['shearling', 'lined'], ['jersey', 'lining'],
        ['jersey', 'lined'], ['textile', 'lining'], ['textile', 'lined'],

        ['gummi', 'sohle'], ['gummi', ' logo'], ['leder', 'futter'], ['leder', 'besatz'], ['canvas', 'besatz'],
        ['leinen', 'futter'], ['baumwoll', 'futter'], ['fleece', 'futter'], ['schafsfell', 'futter'],
        ['kunstfell', 'futter'], ['jersey', 'futter'], ['lammfell', 'futter'],

        ['borracha', 'sola'], ['borracha', 'logotipo']
    ]

    wanted_regex=[
        r'(\S+) upper', #preserve material for upper
    ]
    # HUGO BOSS SHOES
    regex1 = re.compile(r'(lining:( [\d]+% [\w% ]+,?)+)')
    regex2 = re.compile(r'(sole:( [\d]+% [\w% ]+,?)+)')
    regex3 = re.compile(r'(facing:( [\d]+% [\w% ]+,?)+)')
    regex4 = re.compile(r'(futter:( [\d]+% [\w% ]+,?)+)')
    regex5 = re.compile(r'(sohle:( [\d]+% [\w% ]+,?)+)')
    regex6 = re.compile(r'(besatz:( [\d]+% [\w% ]+,?)+)')

    final_text = ' '

    regexes = [regex1, regex2, regex3, regex4, regex5, regex6]

    for regex in regexes:
        if regex.search(Text):
            Text = Text.replace(regex.search(Text)[0], '')

    for pattern in wanted_regex:
        regex=re.compile(pattern)
        re_search=regex.search(Text)

        if re_search:
            final_text+=re_search.group(0)


    if any(i in Text for i in unwanted_words):
        for word in unwanted_words:
            Text = Text.replace(word, '')


    sentences = re.findall(r'(?:\d[,.]|[^,.])*(?:[,.]|$)', Text)
    for sentence in sentences:
        cond = True
        for combi in unwanted_combi_words:
            if all(i in sentence if i else False for i in combi):
                cond = False
                break
        if cond:
            if not final_text:
                final_text = sentence
            else:
                final_text = final_text + sentence

    return final_text

def remove_indirect_noun(description, nouns=['denim']):
    '''
    Remove phrases which contain indirect nouns
    Example is "denim jeans" is an indirect noun in "wear this with denim jeans"
    Detecting it can cause inaccuracy
    Args:
        description: Product description
        nouns : Keyword for nouns
    Return:
        Cleaned description text
    '''
    verbs=['looks', 'pair', 'style', 'wear', 'dressed', 'team', 'works', 'perfect']
    connectors=['with','alongside']
    compile_verbs='|'.join(verbs)
    compile_nouns=r'|\s'.join(nouns)
    compile_connectors='|'.join(connectors)

    description = description.replace('</li>', ' ')
    description = description.replace('\n', ' ')
    pattern=r'(?:'+compile_verbs+r')(?:\s\w+){0,2} ('+compile_connectors+ r')(?:\s\w+){0,15}(\s'+compile_nouns+')'
    m=re.search(pattern,description, re.IGNORECASE)
    if bool(m):
        # print('Detect & Remove Indirect Noun:', m.group(0))
        description=description.replace(m.group(0), '')
    return description

def SetMaterials(Text, s_key, materials, category, subcategories, test = None):
    obj = g_material_layers.get(s_key, '')
    if not obj and not test:
        return
    if test:
        s = test.get('materials',[])
    else:
        s = obj.get('materials',[])
    for i in s:
        if any(j in category for j in s[i].get('not_category', '')):
            continue
        if any(j in category for j in s[i].get('any_category', '')):
            materials.append(i)
            continue
        if any(j in subcategories for j in s[i].get('not_style', '')):
            continue
        if any(j in subcategories for j in s[i].get('any_style', '')):
            materials.append(i)
            continue
        if any(j in Text for j in s[i].get('not', '')):
            continue
        if any(j in Text for j in s[i].get('any', '')):
            materials.append(i)
            continue
        if all(j in Text if j else False for j in s[i].get('all',[''])):
            materials.append(i)
    return


#----------------Category------|---Sub Category------|--Keywords------------------|
'''
g_material_layers['General'] = {
    'materials': {
        'Acetate': {
			'any': [' acetate']
		}
    }
}
'''

g_material_layers['Clothing'] = {
    'materials': {
        'Acetate': {'any': [' acetate', 'acetato', 'あせてーと', 'アセテート']},
        'Acrylic': { 'any': [ ' acrylic', ' acrílico', 'acrilico',
                           'あくりる', 'アクリル']},
        'Brass': { 'any': [' brass', ' latão', 'しんちゅう', 'シンチュウ', '真鍮'],
                'not': ['brass button', '真鍮のボタン']},
        'Calf Hair': {'any': ['calf hair', 'pêlo', 'ふくらはぎのけ', '脹脛の毛']},
        'Canvas': {'any': [' canvas', ' tela ', 'かんばす', 'カンバス']},
        'Cashmere': {'any': ['cashmere', 'かしみあ', 'カシミア']},
        'Chambray': {'any': ['chambray', 'cambraia', 'シャンブレー']},
        'Chiffon': {'any': ['chiffon', 'しふぉん', 'シフォン']},
        'Chino': {'any': ['chino', 'チノ']},
        'Corduroy': { 'any': [ 'corduroy', 'courdroy', 'veludo cotelê',
                            'こーでゅろい', 'コーデュロイ']},
        'Cotton': { 'any': [ ' cotton', 'katun', 'baumwoll', 'algodão',
                          'algod', 'algodao', 'わた', 'ワタ', '綿', 'コットン']},
        'Crepe': {'any': ['crepe', 'くれーぷ', 'クレープ']},
        'Denim': { 'any': ['denim', 'bahan jean', 'でにむ', 'デニム'],
                'not': [ 'faux', 'denim fit', 'denim design motif',
                         'denimist', 'dr denim', 'shawl', 'scarve',
                         'scarf', 'hijab', 'swimsuit', 'bikini',
                         'swimwear', 'palmetto dress',
                         'でにむのでざいんもちーふ', 'デニムのデザインモチーフ', 'でにむふぃっと',
                         'デニムフィット', 'フェイク'],
                'not_style': ['T-Shirts', 'Polos']},
        'Faux': { 'any': [' faux', 'フェイク'],
               'not': [ 'faux fur', 'faux leather',
                        'faux shearling', 'faux wrap',
                        'faux saffiano leather', ' faux pearl ',
                        'ごうせいひかく', 'ゴウセイヒカク', '合成皮革', 'にせしんじゅ',
                        'ニセシンジュ', '偽真珠', 'にせせんだん', 'ニセセンダン', '偽剪断',
                        'にせなっぷ', 'ニセラップ', '偽ラップ', '偽ものの毛皮']},
        'Faux Fur': { 'all': [ ' faux', ' fur ', 'けがわ', 'カガワ', '毛皮',
                            'フェイク'],
                   'any': ['kunstfell', 'pelúcia pelo']},
        'Faux Leather': { 'all': [ ' faux', ' leather ', 'かわ', 'カワ',
                                '革', 'フェイク'],
                       'any': ['kunstleder', 'pelúcia couro']},
        'Faux Pearl': { 'any': [ ' faux pearl ', 'にせしんじゅ', 'ニセシンジュ',
                              '偽真珠']},
        'Faux Shearling': { 'all': [ ' faux', 'shearling', 'しゃーりんぐ',
                                  'シャーリング', 'フェイク']},
        'Fleece': {'any': ['fleece', 'ふりーす', 'フリース']},
        'French Terry': {'any': [' french terry ', 'フレンチテリー']},
        'Georgette': {'any': ['georgette', 'じょーぜっと', 'ジョーゼット']},
        'Hemp': {'any': [' hemp ', ' canhamo ', 'あさ', 'アサ', '麻']},
        'Jacquard': { 'any': [ 'jacquard', 'brocade', 'damask',
                            'ぶろけーど', 'ブロケード', 'だますく', 'ダマスク',
                            'ジャカード']},
        'Jersey': {'any': ['jersey', 'じゃーじ', 'ジャージ']},
        'Jute': { 'any': [ 'jute', 'burlap', ' juta ', 'sisal',
                        'ばーらっぷ', 'バーラップ', 'じゅーと', 'ジュート']},
        'Latex': { 'any': [' latex', 'らてっくす', 'ラテックス'],
                'not': [ 'latex case', 'no latex', 'latex pouch',
                         'らてっくすけーす', 'ラテックスケース', 'らてっくすぱうち',
                         'ラテックスパウチ', 'らてっくすなし', 'ラテックスなし']},
        'Leather': { 'any': [ ' leather', 'leder', 'cow skin',
                           'cowskin', 'calf skin', 'calfskin',
                           'lamb skin', 'lambskin', 'lammfell',
                           ' couro ', 'ふくらはぎのひふ', '脹脛の皮膚', 'かーふすきん',
                           'カーフスキン', 'ぎゅうかわ', 'ギュウカワ', '牛皮',
                           'かうすきん', 'カウスキン', 'らむのかわ', 'ラムノカワ',
                           'ラムの皮', 'らむすきん', 'ラムスキン', 'かわ', 'カワ',
                           '革', 'レザー'],
                  'not': [ 'leather look', 'faux leather',
                           'faux skin', 'faux cow leather',
                           'kunstleder', 'faux cow skin',
                           'faux cowskin', 'faux calf leather',
                           'faux calf skin', 'faux calfskin',
                           'faux lamb leather', 'faux lambskin',
                           'faux lamb skin', 'ふぇいくかーふれざー',
                           'フェイクカーフレザー', 'にせふくらはぎのひふ', 'ニセフクラハギノヒフ',
                           '偽脹脛の皮膚', 'にせのかーふすきん', 'ニセノカーフスキン',
                           '偽のカーフスキン', 'ごうせいひかく', 'ゴウセイヒカク', '合成皮革',
                           'にせぎゅうかわ', 'ニセギュウカワ', '偽牛皮',
                           'ふぇいくれいむれさー', 'フェイクレイムレザー', 'にせらむのかわ',
                           'ニセラムノカワ', '偽ラムの皮', 'にせらむすきん', 'ニセラムスキン',
                           '偽ラムスキン', 'にせひかく', 'ニセヒカク', '偽皮膚',
                           'かわのようなひょうじょう', 'カワノヨウナヒョウジョウ',
                           '革のような表情']},
        'Linen': { 'any': [ ' linen', 'leinen', ' linho ', 'あさ', 'アサ',
                         '麻', 'リネン']},
        'Microfibre': { 'any': [ 'microfibre', 'microfiber',
                              'micro fiber', 'micro fibre',
                              'microfibra', 'まいくろふぁいばー',
                              'マイクロファイバー', '超極細繊維']},
        'Modal': {'any': [' modal', 'モーダル']},
        'Neoprene': {'any': ['neoprene', 'neopren', 'ねおぷれん', 'ネオプレン']},
        'Nylon': {'any': ['nylon', 'ないろん', 'ナイロン']},
        'Organza': { 'any': ['organza', 'おるがんざ', 'オルガンザ'],
                  'not': ['bracelet', 'うでわ', 'ウデワ', '腕輪']},
        'Plisse': {'any': ['plisse', 'plissado']},
        'Polyamide': { 'any': [ 'polyamide', 'polyamid', 'polymide',
                             'poliamida', 'ぽりあもど', 'ポリアミド', 'ぽりみど',
                             'ポリミド']},
        'Polyblend': {'any': ['polyblend', 'ぽりぶれんど', 'ポリブレンド']},
        'Polyester': { 'any': [ ' poly cotton ', 'polyester',
                             'poliester', 'poli ster', 'ぽりえすてる',
                             'ポリエステル', 'ポリコットン']},
        'Polypropylene': { 'any': [ 'polypropylene', 'polipropileno',
                                 'ぽりぷろぴれん', 'ポリプロピレン']},
        'Polyurethane': { 'any': [ 'polyurethane', ' pu ',
                                'polyurethan', 'poliuretano',
                                'ぽりうれたん', 'ポリウレタン']},
        'Polyvinylchloride': { 'any': [ 'polyvinylchloride', 'pvc',
                                     'polyvinyl chloride', 'vinyl',
                                     'cloreto de polivinil',
                                     'ぽりえんかびにる', 'ポリエンカブニル',
                                     'ポリ塩化ビニル', 'ポリエンカビニル', 'びにる',
                                     'ビニル']},
        'Rayan': { 'any': [ ' rayan ', ' modal ', ' tencel ',
                         ' lyocell ', 'リヨセル', 'モーダル', 'テンセル']},
        'Resin': {'any': [' resin', ' resina', 'じゅし', 'ジュシ', '樹脂']},
        'Satin': {'any': ['satin', 'cetim', 'さてん', 'サテン']},
        'Sequin': {'any': ['sequin', 'lantejoula', 'しーくいん', 'シークイン']},
        'Shearling': { 'any': [ 'shearling', 'lã de carneiro',
                             'しゃーりんぐ', 'シャーリング'],
                    'not': ['faux', 'pelúcia', 'フェイク']},
        'Sheepskin': { 'any': ['sheepskin', 'schafleder', '羊皮'],
                    'not': ['faux', 'pelúcia', 'フェイク']},
        'Silicone': { 'any': [ ' silicone ', ' silikone ', 'しりこーん',
                            'シリコーン']},
        'Silk': { 'any': [ ' silk ', 'seide', ' seda ', 'きぬ', 'キヌ',
                        '絹'],
               'not': [ ' silky', 'siksilk', 'silksilk',
                        'silk screen printing', 'しるくすくりーんいんさつ',
                        'シルクスクリーンインサツ', 'シルクスクリーン印刷', 'きぬの', 'キヌノ',
                        '絹の']},
        'Snakeskin': { 'all': [ 'genuine', 'python', 'ほんものの', 'ホンモノノ',
                             '本物の', 'にしきへび', 'ニシキヘビ'],
                    'any': [ 'snakeskin', 'pele de cobra', 'へびかわ',
                             'ヘビカワ', '蛇皮'],
                    'not': [ 'snakeskin look', 'snakeskin textured',
                             'へびのようなかお', 'ヘビノヨウナカオ', '蛇のような顔',
                             'すねーくすきんてくすちゃ', 'スネークスキンテクスチャ']},
        'Spandex': { 'any': [ 'spandex', 'elastane', 'elasthan',
                           ' lycra', 'elastano', 'えらすたん', 'エラスタン',
                           'らいくら', 'ライクラ', 'すぱんでっくす', 'スパンデックス']},
        'Sterling Silver': { 'all': [ 'sterling', 'silver', 'ぎん', 'ギン',
                                   '銀', 'ぽんど', 'ポンド']},
        'Suede': { 'any': [' suede', 'veloursleder', 'すえーど', 'スエード'],
                'not': [ 'suede look', 'すえーどちょう', 'スエードチョウ',
                         'スエード調']},
        'Synthetic': { 'any': [ 'synthetic', 'sintético', 'sint tico',
                             'ごうせいの', 'ゴウセイノ', '合成の'],
                    'not': [ 'synthetic case', 'ごうせいかく', 'ゴウセイカク',
                             '合成格']},
        'Taffeta': {'any': ['taffeta', 'tafetá', 'たふた', 'タフタ']},
        'Textile': { 'any': [ 'textile', 'textil', 'tekstil', 'おりもの',
                           'オリモノ', '織物']},
        'Tulle': {'any': ['tulle', ' tule ', 'ちゅーる', 'チュール']},
        'Tweed': {'any': ['tweed', 'ついーど', 'ツイード']},
        'Velvet': { 'any': [ 'velvet', ' samt ', ' veludo ', 'べるべっと',
                          'ベルベット'],
                 'not': [ 'faux', 'bracelet', 'velvet mirror',
                          'pelúcia', 'うでわ', 'ウデワ', '腕輪', 'びろーどかがみ',
                          'ビロードカガミ', 'ビロード鏡', 'フェイク']},
        'Viscose': { 'any': [ 'viscose', 'viskose', 'rayon', 'びすこーす',
                           'ビスコース']},
        'Wool': { 'any': [ 'wool', 'flanel', ' lã ', 'ようひ', 'ヨウヒ',
                        '羊毛', 'ウール']}
    }
}

g_material_layers['Shoes'] = {
    'materials': {
        'Acetate': {'any': [' acetate', ' acetato', 'あせてーと', 'アセテート']},
        'Acrylic': { 'any': [ ' acrylic', ' acrílico', 'acrilico',
                           'あくりる', 'アクリル']},
        'Calf Hair': { 'any': [ 'calf hair', 'calf fur', ' pêlo ',
                             'ふくらはぎのけ', '脹脛の毛', '子牛の毛皮']},
        'Canvas': {'any': [' canvas', ' tela ', 'かんばす', 'カンバス']},
        'Cashmere': {'any': ['cashmere', 'かしみあ', 'カシミア']},
        'Chambray': {'any': ['chambray', 'cambraia', 'シャンブレー']},
        'Chiffon': {'any': ['chiffon', 'しふぉん', 'シフォン']},
        'Corduroy': { 'any': [ 'corduroy', 'veludo cotelê', 'こーでゅろい',
                            'コーデュロイ']},
        'Cotton': { 'any': [ ' cotton', 'katun', 'baumwoll', 'algodão',
                          'algod', 'algodao', 'わた', 'ワタ', '綿', 'コットン']},
        'Crepe': {'any': ['crepe', 'くれーぷ', 'クレープ']},
        'Croslite': {'any': ['croslite']},
        'Faux': { 'any': [' faux', 'フェイク'],
               'not': [ 'faux fur', 'faux leather',
                        'faux shearling', 'faux wrap',
                        'faux saffiano leather', 'ごうせいひかく',
                        'ゴウセイヒカク', '合成皮革', 'にせせんだん', 'ニセセンダン',
                        '偽剪断', 'にせなっぷ', 'ニセラップ', '偽ラップ',
                        '偽ものの毛皮']},
        'Faux Fur': { 'all': [ ' faux', ' fur ', 'けがわ', 'カガワ', '毛皮',
                            'フェイク'],
                   'any': ['kunstfell', 'pelúcia pelo'],
                   'not': ['calf fur faux leather']},
        'Faux Leather': { 'all': [ ' faux', ' leather ', 'かわ', 'カワ',
                                '革', 'フェイク'],
                       'any': ['kunstleder', 'pelúcia couro']},
        'Faux Shearling': { 'all': [ ' faux', 'shearling', 'しゃーりんぐ',
                                  'シャーリング', 'フェイク']},
        'Fleece': {'any': ['fleece', 'ふりーす', 'フリース']},
        'Hemp': {'any': [' hemp ', 'canhamo', 'あさ', 'アサ', '麻']},
        'Jacquard': { 'any': [ 'jacquard', 'brocade', 'damask',
                            'ぶろけーど', 'ブロケード', 'だますく', 'ダマスク',
                            'ジャカード']},
        'Jersey': {'any': ['jersey', 'じゃーじ', 'ジャージ']},
        'Jute': { 'any': [ 'jute', 'burlap', ' juta ', 'sisal',
                        'ばーらっぷ', 'バーラップ', 'じゅーと', 'ジュート']},
        'Latex': { 'any': [' latex', 'らてっくす', 'ラテックス'],
                'not': [ 'latex case', 'no latex', 'latex pouch',
                         'らてっくすけーす', 'ラテックスケース', 'らてっくすぱうち',
                         'ラテックスパウチ', 'らてっくすなし', 'ラテックスなし']},
        'Leather': { 'any': [ ' leather', 'leder', 'cow skin',
                           'cowskin', 'calf skin', 'calfskin',
                           'lamb skin', 'lambskin', 'lammfell',
                           ' couro ', 'ふくらはぎのひふ', '脹脛の皮膚', 'かーふすきん',
                           'カーフスキン', 'ぎゅうかわ', 'ギュウカワ', '牛皮',
                           'かうすきん', 'カウスキン', 'らむのかわ', 'ラムノカワ',
                           'ラムの皮', 'らむすきん', 'ラムスキン', 'かわ', 'カワ',
                           '革', 'レザー'],
                  'not': [ 'leather look', 'faux leather',
                           'faux skin', 'faux cow leather',
                           'kunstleder', 'faux cow skin',
                           'faux cowskin', 'faux calf leather',
                           'faux calf skin', 'faux calfskin',
                           'faux lamb leather', 'faux lambskin',
                           'faux lamb skin', 'ふぇいくかーふれざー',
                           'フェイクカーフレザー', 'にせふくらはぎのひふ', 'ニセフクラハギノヒフ',
                           '偽脹脛の皮膚', 'にせのかーふすきん', 'ニセノカーフスキン',
                           '偽のカーフスキン', 'ごうせいひかく', 'ゴウセイヒカク', '合成皮革',
                           'にせぎゅうかわ', 'ニセギュウカワ', '偽牛皮',
                           'ふぇいくれいむれさー', 'フェイクレイムレザー', 'にせらむのかわ',
                           'ニセラムノカワ', '偽ラムの皮', 'にせらむすきん', 'ニセラムスキン',
                           '偽ラムスキン', 'にせひかく', 'ニセヒカク', '偽皮膚',
                           'かわのようなひょうじょう', 'カワノヨウナヒョウジョウ',
                           '革のような表情']},
        'Linen': { 'any': [ ' linen', 'leinen', 'linho', 'あさ', 'アサ',
                         '麻', 'リネン']},
        'Microfibre': { 'any': [ 'microfibre', 'microfiber',
                              'micro fiber', 'micro fibre',
                              'microfibra', 'まいくろふぁいばー',
                              'マイクロファイバー', '超極細繊維']},
        'Modal': {'any': [' modal', 'モーダル']},
        'Neoprene': {'any': ['neoprene', 'neopren', 'ねおぷれん', 'ネオプレン']},
        'Nylon': {'any': ['nylon', 'ないろん', 'ナイロン']},
        'Organza': { 'any': ['organza', 'おるがんざ', 'オルガンザ'],
                  'not': ['bracelet', 'うでわ', 'ウデワ', '腕輪']},
        'Plastic': { 'any': [ ' plastic', ' plastik', 'kunststoff',
                           'plástico', 'ぷらすちっく', 'プラスチック'],
                  'not': [ 'plastic case', 'plastic pouch',
                           'avoid plastic', 'plastic fastener',
                           'ぷらすちっくをさける', 'プラスチックヲサケル', 'プラスチックを避ける',
                           'ぷらすちっくけーす', 'プラスチックケース', 'ぷらすちっくふぁすなー',
                           'プラスチックファスナー', 'ぷらすちっくぶくろ', 'プラスチックブクロ',
                           'プラスチック袋']},
        'Polyamide': { 'any': [ 'polyamide', 'polyamid', 'polymide',
                             'poliamida', 'ぽりあもど', 'ポリアミド', 'ぽりみど',
                             'ポリミド']},
        'Polyblend': {'any': ['polyblend', 'ぽりぶれんど', 'ポリブレンド']},
        'Polyester': { 'any': [ 'polyester', 'poliester', 'poli ster',
                             'ぽりえすてる', 'ポリエステル']},
        'Polyethylene': { 'any': [ 'polyethylene', 'polietileno',
                                'ポリエチレン']},
        'Polypropylene': { 'any': [ 'polypropylene', 'polipropileno',
                                 'ぽりぷろぴれん', 'ポリプロピレン']},
        'Polyurethane': { 'any': [ 'polyurethane', ' pu ',
                                'polyurethan', 'poliuretano',
                                'ぽりうれたん', 'ポリウレタン']},
        'Polyvinylchloride': { 'any': [ 'polyvinylchloride', 'pvc',
                                     'polyvinyl chloride',
                                     'polyvinylchlorid', 'vinyl',
                                     'cloreto de polivinil',
                                     'ぽりえんかびにる', 'ポリエンカブニル',
                                     'ポリ塩化ビニル', 'ポリエンカビニル', 'びにる',
                                     'ビニル']},
        'Resin': {'any': [' resin', ' resina', 'じゅし', 'ジュシ', '樹脂']},
        'Rubber': { 'any': [' rubber', ' borracha', 'ごむ', 'ゴム'],
                 'not': ['rubber patch', 'ごむぱっち', 'ゴムパッチ']},
        'Satin': {'any': ['satin', 'cetim', 'さてん', 'サテン']},
        'Sequin': {'any': ['sequin', 'lantejoula', 'しーくいん', 'シークイン']},
        'Shearling': { 'any': [ 'shearling', 'lã de carneiro',
                             'しゃーりんぐ', 'シャーリング'],
                    'not': ['faux', 'pelúcia', 'フェイク']},
        'Sheepskin': { 'any': ['sheepskin', 'schafleder', '羊皮'],
                    'not': ['faux', 'pelúcia', 'フェイク']},
        'Silicone': {'any': ['silicone', 'silikon', 'しりこーん', 'シリコーン']},
        'Silk': { 'any': [' silk ', 'seide', ' seda', 'きぬ', 'キヌ', '絹'],
               'not': [ ' silky', 'siksilk', 'silksilk',
                        'silk screen printing', 'しるくすくりーんいんさつ',
                        'シルクスクリーンインサツ', 'シルクスクリーン印刷', 'きぬの', 'キヌノ',
                        '絹の']},
        'Snakeskin': { 'all': [ 'genuine', 'python', 'ほんものの', 'ホンモノノ',
                             '本物の', 'にしきへび', 'ニシキヘビ'],
                    'any': [ 'snakeskin', 'pele de cobra', 'へびかわ',
                             'ヘビカワ', '蛇皮'],
                    'not': [ 'snakeskin look', 'snakeskin textured',
                             'へびのようなかお', 'ヘビノヨウナカオ', '蛇のような顔',
                             'すねーくすきんてくすちゃ', 'スネークスキンテクスチャ']},
        'Spandex': { 'any': [ 'spandex', 'elastane', 'elasthan',
                           ' lycra', 'elastano', 'えらすたん', 'エラスタン',
                           'らいくら', 'ライクラ', 'すぱんでっくす', 'スパンデックス']},
        'Suede': { 'any': [' suede', 'veloursleder', 'すえーど', 'スエード'],
                'not': [ 'suede look', 'すえーどちょう', 'スエードチョウ',
                         'スエード調']},
        'Synthetic': { 'any': [ ' synthetic', 'sintético', 'sint tico',
                             'ごうせいの', 'ゴウセイノ', '合成の']},
        'Textile': { 'any': [ 'textile', 'textil', 'tekstil', 'おりもの',
                           'オリモノ', '織物']},
        'Tulle': {'any': ['tulle', ' tule ', 'ちゅーる', 'チュール']},
        'Tweed': {'any': ['tweed', 'ついーど', 'ツイード']},
        'Velvet': { 'any': [ 'velvet', ' samt ', 'veludo', 'べるべっと',
                          'ベルベット'],
                 'not': [ 'faux', 'bracelet', 'velvet mirror',
                          'うでわ', 'ウデワ', '腕輪', 'びろーどかがみ', 'ビロードカガミ',
                          'ビロード鏡', 'フェイク']},
        'Viscose': { 'any': [ 'viscose', 'viskose', 'rayon', 'びすこーす',
                           'ビスコース']},
        'Wool': { 'any': [ 'wool', 'flanel', ' lã ', 'ようひ', 'ヨウヒ',
                        '羊毛', 'ウール']}
    }
}

g_material_layers['Eyewear'] = {
    'materials': {
        'Acetate': {'any': [' acetate', ' acetato', 'あせてーと', 'アセテート']},
        'Acrylic': { 'any': [ ' acrylic', ' acrílico', 'acrilico',
                           'あくりる', 'アクリル']},
        'Buffalo Horn': {'any': [' buffalo horn ', 'chifre', '水牛の角']},
        'Cotton': { 'any': [ ' cotton', 'katun', 'baumwoll', 'algodão',
                          'algod', 'algodao', 'わた', 'ワタ', '綿', 'コットン']},
        'Faux': { 'any': [' faux', 'フェイク'],
               'not': [ 'faux fur', 'faux leather',
                        'faux shearling', 'faux wrap',
                        'faux saffiano leather', 'ごうせいひかく',
                        'ゴウセイヒカク', '合成皮革', 'にせせんだん', 'ニセセンダン',
                        '偽剪断', 'にせなっぷ', 'ニセラップ', '偽ラップ',
                        '偽ものの毛皮']},
        'Metal': { 'any': [ ' metal ', ' steel', 'titanium',
                         'beryllium', 'monel', 'aluminium',
                         'flexon', 'titânio', 'níquel', 'berílio',
                         'alumíniom', 'きんぞく', 'キンゾク', '金属', 'すちーる',
                         'スチール', 'アルミニウム', 'ベリリウム', 'モネル', 'チタン']},
        'Nylon': {'any': ['nylon', 'ないろん', 'ナイロン']},
        'Plastic': { 'any': [ ' plastic', ' plastik', 'kunststoff',
                           'plástico', 'ぷらすちっく', 'プラスチック'],
                  'not': [ 'plastic case', 'plastic pouch',
                           'avoid plastic', 'plastic fastener',
                           'ぷらすちっくをさける', 'プラスチックヲサケル', 'プラスチックを避ける',
                           'ぷらすちっくけーす', 'プラスチックケース', 'ぷらすちっくふぁすなー',
                           'プラスチックファスナー', 'ぷらすちっくぶくろ', 'プラスチックブクロ',
                           'プラスチック袋']},
        'Polyamide': { 'any': [ 'polyamide', 'polyamid', 'polymide',
                             'poliamida', 'ぽりあもど', 'ポリアミド', 'ぽりみど',
                             'ポリミド']},
        'Polycarbonate': { 'any': [ 'polycarbonate', 'policarbonato',
                                 'ポリカーボネート']},
        'Polyester': { 'any': [ 'polyester', 'poliester', 'poli ster',
                             'ぽりえすてる', 'ポリエステル']},
        'Polypropylene': { 'any': [ 'polypropylene', 'polipropileno',
                                 'ぽりぷろぴれん', 'ポリプロピレン']},
        'Polyurethane': { 'any': [ 'polyurethane', ' pu ',
                                'polyurethan', 'poliuretano',
                                'ぽりうれたん', 'ポリウレタン']},
        'Polyvinylchloride': { 'any': [ 'polyvinylchloride', 'pvc',
                                     'polyvinyl chloride', 'vinyl',
                                     'cloreto de polivinil',
                                     'ぽりえんかびにる', 'ポリエンカブニル',
                                     'ポリ塩化ビニル', 'ポリエンカビニル', 'びにる',
                                     'ビニル']},
        'Resin': {'any': [' resin', 'resina', 'じゅし', 'ジュシ', '樹脂']},
        'Silk': { 'any': [' silk ', 'seide', ' seda', 'きぬ', 'キヌ', '絹'],
               'not': [ ' silky', 'siksilk', 'silksilk',
                        'silk screen printing', 'しるくすくりーんいんさつ',
                        'シルクスクリーンインサツ', 'シルクスクリーン印刷', 'きぬの', 'キヌノ',
                        '絹の']},
        'Synthetic': { 'any': [ 'synthetic', 'sintético', 'sint tico',
                             'ごうせいの', 'ゴウセイノ', '合成の'],
                    'not': [ 'synthetic case', 'ごうせいかく', 'ゴウセイカク',
                             '合成格']},
        'Velvet': { 'any': [ 'velvet', ' samt ', 'veludo', 'べるべっと',
                          'ベルベット'],
                 'not': [ 'faux', 'bracelet', 'velvet mirror',
                          'うでわ', 'ウデワ', '腕輪', 'びろーどかがみ', 'ビロードカガミ',
                          'ビロード鏡', 'フェイク']},
        'Viscose': { 'any': [ 'viscose', 'viskose', 'rayon', 'びすこーす',
                           'ビスコース']},
        'Wood': {'any': [' wood ', ' madeira ', '木材']}
    }
}

g_material_layers['Accessories'] = {
    'materials': {
        'Acetate': {'any': [' acetate', ' acetato', 'あせてーと', 'アセテート']},
        'Acrylic': { 'any': [ ' acrylic', ' acrílico', 'acrilico',
                           'あくりる', 'アクリル']},
        'Calf Hair': { 'any': [ 'calf hair', ' pêlo ', 'ふくらはぎのけ',
                             '脹脛の毛']},
        'Canvas': {'any': [' canvas', ' tela ', 'かんばす', 'カンバス']},
        'Cashmere': {'any': ['cashmere', 'かしみあ', 'カシミア']},
        'Chambray': {'any': ['chambray', 'cambraia', 'シャンブレー']},
        'Chiffon': {'any': ['chiffon', 'しふぉん', 'シフォン']},
        'Corduroy': { 'any': [ 'corduroy', 'veludo cotelê', 'こーでゅろい',
                            'コーデュロイ']},
        'Cotton': { 'any': [ ' cotton', 'katun', 'baumwoll', 'algodão',
                          'algod', 'algodao', 'わた', 'ワタ', '綿', 'コットン']},
        'Crepe': {'any': ['crepe', 'くれーぷ', 'クレープ']},
        'Denim': { 'any': ['denim', 'でにむ', 'デニム'],
                'not': [ 'faux', 'denim fit', 'denim design motif',
                         'pelúcia', 'でにむのでざいんもちーふ', 'デニムのデザインモチーフ',
                         'でにむふぃっと', 'デニムフィット', 'フェイク']},
        'Enamel': {'any': ['enamel', 'esmalte', 'エナメル']},
        'Faux': { 'any': [' faux', 'フェイク'],
               'not': [ 'faux fur', 'faux leather',
                        'faux shearling', 'faux wrap',
                        'faux saffiano leather', 'ごうせいひかく',
                        'ゴウセイヒカク', '合成皮革', 'にせせんだん', 'ニセセンダン',
                        '偽剪断', 'にせなっぷ', 'ニセラップ', '偽ラップ',
                        '偽ものの毛皮']},
        'Faux Fur': { 'all': [ ' faux', ' fur ', 'けがわ', 'カガワ', '毛皮',
                            'フェイク'],
                   'any': ['kunstfell', 'pelúcia pelo'],
                   'not': ['calf fur faux leather']},
        'Faux Leather': { 'all': [ ' faux', ' leather ', 'かわ', 'カワ',
                                '革', 'フェイク'],
                       'any': ['kunstleder', 'pelúcia couro']},
        'Faux Shearling': { 'all': [ ' faux', 'shearling', 'しゃーりんぐ',
                                  'シャーリング', 'フェイク']},
        'Fleece': {'any': ['fleece', 'ふりーす', 'フリース']},
        'Georgette': {'any': ['georgette', 'じょーぜっと', 'ジョーゼット']},
        'Hemp': {'any': [' hemp ', ' canhamo ', 'あさ', 'アサ', '麻']},
        'Jacquard': { 'any': [ 'jacquard', 'brocade', 'damask',
                            'ぶろけーど', 'ブロケード', 'だますく', 'ダマスク',
                            'ジャカード']},
        'Jersey': {'any': ['jersey', 'じゃーじ', 'ジャージ']},
        'Jute': { 'any': [ 'jute', 'burlap', 'juta', 'sisal', 'ばーらっぷ',
                        'バーラップ', 'じゅーと', 'ジュート']},
        'Latex': { 'any': [' latex', 'らてっくす', 'ラテックス'],
                'not': [ 'latex case', 'no latex', 'latex pouch',
                         'らてっくすけーす', 'ラテックスケース', 'らてっくすぱうち',
                         'ラテックスパウチ', 'らてっくすなし', 'ラテックスなし']},
        'Leather': { 'any': [ ' leather', 'leder', 'cow skin',
                           'cowskin', 'calf skin', 'calfskin',
                           'lamb skin', 'lambskin', 'lammfell',
                           ' couro ', 'ふくらはぎのひふ', '脹脛の皮膚', 'かーふすきん',
                           'カーフスキン', 'ぎゅうかわ', 'ギュウカワ', '牛皮',
                           'かうすきん', 'カウスキン', 'らむのかわ', 'ラムノカワ',
                           'ラムの皮', 'らむすきん', 'ラムスキン', 'かわ', 'カワ',
                           '革','レザー'],
                  'not': [ 'leather look', 'faux leather',
                           'faux skin', 'faux cow leather',
                           'kunstleder', 'faux cow skin',
                           'faux cowskin', 'faux calf leather',
                           'faux calf skin', 'faux calfskin',
                           'faux lamb leather', 'faux lambskin',
                           'faux lamb skin', 'ふぇいくかーふれざー',
                           'フェイクカーフレザー', 'にせふくらはぎのひふ', 'ニセフクラハギノヒフ',
                           '偽脹脛の皮膚', 'にせのかーふすきん', 'ニセノカーフスキン',
                           '偽のカーフスキン', 'ごうせいひかく', 'ゴウセイヒカク', '合成皮革',
                           'にせぎゅうかわ', 'ニセギュウカワ', '偽牛皮',
                           'ふぇいくれいむれさー', 'フェイクレイムレザー', 'にせらむのかわ',
                           'ニセラムノカワ', '偽ラムの皮', 'にせらむすきん', 'ニセラムスキン',
                           '偽ラムスキン', 'にせひかく', 'ニセヒカク', '偽皮膚',
                           'かわのようなひょうじょう', 'カワノヨウナヒョウジョウ',
                           '革のような表情']},
        'Linen': { 'any': [ ' linen', 'leinen', 'linho', 'あさ', 'アサ',
                         '麻', 'リネン']},
        'Metal': { 'any': [ ' metal ', ' steel', 'きんぞく', 'キンゾク', '金属',
                         'すちーる', 'スチール'],
                'not': ['faux', ' cap ', 'フェイク']},
        'Microfibre': { 'any': [ 'microfibre', 'microfiber',
                              'micro fiber', 'micro fibre',
                              'microfibra', 'まいくろふぁいばー',
                              'マイクロファイバー', '超極細繊維']},
        'Modal': {'any': [' modal', 'モーダル']},
        'Neoprene': {'any': ['neoprene', 'neopren', 'ねおぷれん', 'ネオプレン']},
        'Nylon': {'any': ['nylon', 'ないろん', 'ナイロン']},
        'Organza': { 'any': ['organza', 'おるがんざ', 'オルガンザ'],
                  'not': ['bracelet', 'うでわ', 'ウデワ', '腕輪']},
        'Plastic': { 'any': [ ' plastic', ' plastik', 'kunststoff',
                           'plástico', 'ぷらすちっく', 'プラスチック'],
                  'not': [ 'plastic case', 'plastic pouch',
                           'avoid plastic', 'plastic fastener',
                           'ぷらすちっくをさける', 'プラスチックヲサケル', 'プラスチックを避ける',
                           'ぷらすちっくけーす', 'プラスチックケース', 'ぷらすちっくふぁすなー',
                           'プラスチックファスナー', 'ぷらすちっくぶくろ', 'プラスチックブクロ',
                           'プラスチック袋']},
        'Polyamide': { 'any': [ 'polyamide', 'polyamid', 'polymide',
                             'poliamida', 'ぽりあもど', 'ポリアミド', 'ぽりみど',
                             'ポリミド']},
        'Polyblend': {'any': ['polyblend', 'ぽりぶれんど', 'ポリブレンド']},
        'Polyester': { 'any': [ 'polyester', 'poliester', 'poli ster',
                             'ぽりえすてる', 'ポリエステル']},
        'Polypropylene': { 'any': [ 'polypropylene', 'polipropileno',
                                 'ぽりぷろぴれん', 'ポリプロピレン']},
        'Polyurethane': { 'any': [ 'polyurethane', ' pu ',
                                'polyurethan', 'poliuretano',
                                'ぽりうれたん', 'ポリウレタン']},
        'Polyvinylchloride': { 'any': [ 'polyvinylchloride', 'pvc',
                                     'polyvinyl chloride', 'vinyl',
                                     'cloreto de polivinil',
                                     'ぽりえんかびにる', 'ポリエンカブニル',
                                     'ポリ塩化ビニル', 'ポリエンカビニル', 'びにる',
                                     'ビニル']},
        'Resin': {'any': [' resin', ' resina', 'じゅし', 'ジュシ', '樹脂']},
        'Rubber': { 'any': [' rubber', 'borracha', 'ごむ', 'ゴム'],
                 'not': ['rubber patch', 'ごむぱっち', 'ゴムパッチ']},
        'Satin': {'any': ['satin', 'cetim', 'さてん', 'サテン']},
        'Sequin': {'any': ['sequin', 'lantejoula', 'しーくいん', 'シークイン']},
        'Shearling': { 'any': [ 'shearling', 'lã de carneiro',
                             'しゃーりんぐ', 'シャーリング'],
                    'not': ['faux', 'pelúcia', 'フェイク']},
        'Sheepskin': { 'any': ['sheepskin', 'schafleder', '羊皮'],
                    'not': ['faux', 'pelúcia', 'フェイク']},
        'Silicone': {'any': ['silicone', 'silikon', 'しりこーん', 'シリコーン']},
        'Silk': { 'any': [' silk ', 'seide', 'seda', 'きぬ', 'キヌ', '絹'],
               'not': [ ' silky', 'siksilk', 'silksilk',
                        'silk screen printing', 'しるくすくりーんいんさつ',
                        'シルクスクリーンインサツ', 'シルクスクリーン印刷', 'きぬの', 'キヌノ',
                        '絹の']},
        'Snakeskin': { 'all': [ 'genuine', 'python', 'ほんものの', 'ホンモノノ',
                             '本物の', 'にしきへび', 'ニシキヘビ'],
                    'any': [ 'snakeskin', 'pele de cobra', 'へびかわ',
                             'ヘビカワ', '蛇皮'],
                    'not': [ 'snakeskin look', 'snakeskin textured',
                             'へびのようなかお', 'ヘビノヨウナカオ', '蛇のような顔',
                             'すねーくすきんてくすちゃ', 'スネークスキンテクスチャ']},
        'Spandex': { 'any': [ 'spandex', 'elastane', 'elasthan',
                           ' lycra', 'elastano', 'えらすたん', 'エラスタン',
                           'らいくら', 'ライクラ', 'すぱんでっくす', 'スパンデックス']},
        'Sterling Silver': { 'all': [ 'sterling', 'silver', 'ぎん', 'ギン',
                                   '銀', 'ぽんど', 'ポンド']},
        'Suede': { 'any': [' suede', 'veloursleder', 'すえーど', 'スエード'],
                'not': [ 'suede look', 'すえーどちょう', 'スエードチョウ',
                         'スエード調']},
        'Synthetic': { 'any': [ 'synthetic', 'sint tico', 'ごうせいの',
                             'ゴウセイノ', '合成の'],
                    'not': [ 'synthetic case', 'ごうせいかく', 'ゴウセイカク',
                             '合成格']},
        'Textile': { 'any': [ 'textile', 'textil', 'tekstil', 'おりもの',
                           'オリモノ', '織物']},
        'Tulle': {'any': ['tulle', 'tule', 'ちゅーる', 'チュール']},
        'Tweed': {'any': ['tweed', 'ついーど', 'ツイード']},
        'Velvet': { 'any': [ 'velvet', ' samt ', 'veludo', 'べるべっと',
                          'ベルベット'],
                 'not': [ 'faux', 'bracelet', 'velvet mirror',
                          'うでわ', 'ウデワ', '腕輪', 'びろーどかがみ', 'ビロードカガミ',
                          'ビロード鏡', 'フェイク']},
        'Viscose': { 'any': [ 'viscose', 'viskose', 'rayon', 'びすこーす',
                           'ビスコース']},
        'Wool': { 'any': [ 'wool', 'flanel', ' lã ', 'ようひ', 'ヨウヒ',
                        '羊毛', 'ウール']}
    }
}

g_material_layers['Bags'] = {
    'materials': {
        'Acetate': {'any': [' acetate', ' acetato', 'あせてーと', 'アセテート']},
        'Acrylic': { 'any': [ ' acrylic', ' acrílico', 'acrilico',
                           'あくりる', 'アクリル']},
        'Calf Hair': {'any': ['calf hair', 'pêlo', 'ふくらはぎのけ', '脹脛の毛']},
        'Canvas': {'any': [' canvas', ' tela ', 'かんばす', 'カンバス']},
        'Cashmere': {'any': ['cashmere', 'かしみあ', 'カシミア']},
        'Chambray': {'any': ['chambray', 'cambraia', 'シャンブレー']},
        'Chiffon': {'any': ['chiffon', 'しふぉん', 'シフォン']},
        'Corduroy': { 'any': [ 'corduroy', 'veludo cotelê', 'こーでゅろい',
                            'コーデュロイ']},
        'Cotton': { 'any': [ ' cotton', 'katun', 'baumwoll', 'algodão',
                          'algod', 'algodao', 'わた', 'ワタ', '綿', 'コットン']},
        'Crepe': {'any': ['crepe', 'くれーぷ', 'クレープ']},
        'Denim': { 'any': ['denim', 'でにむ', 'デニム'],
                'not': [ 'faux', 'denim fit', 'denim design motif',
                         'でにむのでざいんもちーふ', 'デニムのデザインモチーフ', 'でにむふぃっと',
                         'デニムフィット', 'フェイク']},
        'Faux': { 'any': [' faux', 'フェイク'],
               'not': [ 'faux fur', 'faux leather',
                        'faux shearling', 'faux wrap',
                        'faux saffiano leather', 'ごうせいひかく',
                        'ゴウセイヒカク', '合成皮革', 'にせせんだん', 'ニセセンダン',
                        '偽剪断', 'にせなっぷ', 'ニセラップ', '偽ラップ',
                        '偽ものの毛皮']},
        'Faux Fur': { 'all': [ ' faux', ' fur ', 'けがわ', 'カガワ', '毛皮',
                            'フェイク'],
                   'any': ['kunstfell', 'pelúcia pelo'],
                   'not': ['calf fur faux leather']},
        'Faux Leather': { 'all': [ ' faux', ' leather ', 'かわ', 'カワ',
                                '革', 'フェイク'],
                       'any': ['kunstleder', 'pelúcia couro']},
        'Faux Shearling': { 'all': [ ' faux', 'shearling', 'しゃーりんぐ',
                                  'シャーリング', 'フェイク']},
        'Fleece': {'any': ['fleece', 'ふりーす', 'フリース']},
        'Hemp': {'any': [' hemp ', ' canhamo ', 'あさ', 'アサ', '麻']},
        'Jacquard': { 'any': [ 'jacquard', 'brocade', 'damask',
                            'ぶろけーど', 'ブロケード', 'だますく', 'ダマスク',
                            'ジャカード']},
        'Jersey': {'any': ['jersey', 'じゃーじ', 'ジャージ']},
        'Jute': { 'any': [ 'jute', 'burlap', ' juta ', 'sisal',
                        'ばーらっぷ', 'バーラップ', 'じゅーと', 'ジュート']},
        'Leather': { 'any': [ ' leather', 'leder', 'cow skin',
                           'cowskin', 'calf skin', 'calfskin',
                           'lamb skin', 'lambskin', 'lammfell',
                           ' couro', 'ふくらはぎのひふ', '脹脛の皮膚', 'かーふすきん',
                           'カーフスキン', 'ぎゅうかわ', 'ギュウカワ', '牛皮',
                           'かうすきん', 'カウスキン', 'らむのかわ', 'ラムノカワ',
                           'ラムの皮', 'らむすきん', 'ラムスキン', 'かわ', 'カワ',
                           '革', 'レザー'],
                  'not': [ 'leather look', 'faux leather',
                           'faux skin', 'faux cow leather',
                           'kunstleder', 'faux cow skin',
                           'faux cowskin', 'faux calf leather',
                           'faux calf skin', 'faux calfskin',
                           'faux lamb leather', 'faux lambskin',
                           'faux lamb skin', 'ふぇいくかーふれざー',
                           'フェイクカーフレザー', 'にせふくらはぎのひふ', 'ニセフクラハギノヒフ',
                           '偽脹脛の皮膚', 'にせのかーふすきん', 'ニセノカーフスキン',
                           '偽のカーフスキン', 'ごうせいひかく', 'ゴウセイヒカク', '合成皮革',
                           'にせぎゅうかわ', 'ニセギュウカワ', '偽牛皮',
                           'ふぇいくれいむれさー', 'フェイクレイムレザー', 'にせらむのかわ',
                           'ニセラムノカワ', '偽ラムの皮', 'にせらむすきん', 'ニセラムスキン',
                           '偽ラムスキン', 'にせひかく', 'ニセヒカク', '偽皮膚',
                           'かわのようなひょうじょう', 'カワノヨウナヒョウジョウ',
                           '革のような表情']},
        'Linen': { 'any': [ ' linen', 'leinen', ' linho', 'あさ', 'アサ',
                         '麻', 'リネン']},
        'Microfibre': { 'any': [ 'microfibre', 'microfiber',
                              'micro fiber', 'micro fibre',
                              'microfibra', 'まいくろふぁいばー',
                              'マイクロファイバー', '超極細繊維']},
        'Neoprene': {'any': ['neoprene', 'neopren', 'ねおぷれん', 'ネオプレン']},
        'Nylon': {'any': ['nylon', 'ないろん', 'ナイロン']},
        'Plastic': { 'any': [ ' plastic', ' plastik', 'kunststoff',
                           'plástico', 'ぷらすちっく', 'プラスチック'],
                  'not': [ 'plastic case', 'plastic pouch',
                           'avoid plastic', 'plastic fastener',
                           'ぷらすちっくをさける', 'プラスチックヲサケル', 'プラスチックを避ける',
                           'ぷらすちっくけーす', 'プラスチックケース', 'ぷらすちっくふぁすなー',
                           'プラスチックファスナー', 'ぷらすちっくぶくろ', 'プラスチックブクロ',
                           'プラスチック袋']},
        'Polyamide': { 'any': [ 'polyamide', 'polyamid', 'polymide',
                             'poliamida', 'ぽりあもど', 'ポリアミド', 'ぽりみど',
                             'ポリミド']},
        'Polyblend': {'any': ['polyblend', 'ぽりぶれんど', 'ポリブレンド']},
        'Polyester': { 'any': [ 'polyester', 'poliester', 'poli ster',
                             'ぽりえすてる', 'ポリエステル']},
        'Polypropylene': { 'any': [ 'polypropylene', 'polipropileno',
                                 'ぽりぷろぴれん', 'ポリプロピレン']},
        'Polyurethane': { 'any': [ 'polyurethane', ' pu ',
                                'polyurethan', 'poliuretano',
                                'ぽりうれたん', 'ポリウレタン']},
        'Polyvinylchloride': { 'any': [ 'polyvinylchloride', 'pvc',
                                     'polyvinyl chloride', 'vinyl',
                                     'cloreto de polivinil',
                                     'ぽりえんかびにる', 'ポリエンカブニル',
                                     'ポリ塩化ビニル', 'ポリエンカビニル', 'びにる',
                                     'ビニル']},
        'Resin': {'any': [' resin', 'resina', 'じゅし', 'ジュシ', '樹脂']},
        'Rubber': { 'any': [' rubber', 'borracha', 'ごむ', 'ゴム'],
                 'not': ['rubber patch', 'ごむぱっち', 'ゴムパッチ']},
        'Satin': {'any': ['satin', 'cetim', 'さてん', 'サテン']},
        'Sequin': {'any': ['sequin', 'lantejoula', 'しーくいん', 'シークイン']},
        'Shearling': { 'any': ['shearling', 'しゃーりんぐ', 'シャーリング'],
                    'not': ['faux', 'フェイク']},
        'Sheepskin': { 'any': ['sheepskin', 'schafleder', '羊皮'],
                    'not': ['faux', 'フェイク']},
        'Silicone': {'any': ['silicone', 'silikon', 'しりこーん', 'シリコーン']},
        'Silk': { 'any': [' silk ', 'seide', 'seda', 'きぬ', 'キヌ', '絹'],
               'not': [ ' silky', 'siksilk', 'silksilk',
                        'silk screen printing', 'しるくすくりーんいんさつ',
                        'シルクスクリーンインサツ', 'シルクスクリーン印刷', 'きぬの', 'キヌノ',
                        '絹の']},
        'Snakeskin': { 'all': [ 'genuine', 'python', 'ほんものの', 'ホンモノノ',
                             '本物の', 'にしきへび', 'ニシキヘビ'],
                    'any': ['snakeskin', 'へびかわ', 'ヘビカワ', '蛇皮'],
                    'not': [ 'snakeskin look', 'snakeskin textured',
                             'へびのようなかお', 'ヘビノヨウナカオ', '蛇のような顔',
                             'すねーくすきんてくすちゃ', 'スネークスキンテクスチャ']},
        'Spandex': { 'any': [ 'spandex', 'elastane', 'elasthan',
                           ' lycra', 'elastano', 'えらすたん', 'エラスタン',
                           'らいくら', 'ライクラ', 'すぱんでっくす', 'スパンデックス']},
        'Sterling Silver': { 'all': [ 'sterling', 'silver', 'ぎん', 'ギン',
                                   '銀', 'ぽんど', 'ポンド']},
        'Suede': { 'any': [' suede', 'veloursleder', 'すえーど', 'スエード'],
                'not': [ 'suede look', 'すえーどちょう', 'スエードチョウ',
                         'スエード調']},
        'Synthetic': { 'any': [ 'synthetic', 'sintético', 'sint tico',
                             'ごうせいの', 'ゴウセイノ', '合成の'],
                    'not': [ 'synthetic case', 'ごうせいかく', 'ゴウセイカク',
                             '合成格']},
        'Taffeta': {'any': ['taffeta', 'tafetá', 'たふた', 'タフタ']},
        'Textile': { 'any': [ 'textile', 'textil', 'tekstil', 'おりもの',
                           'オリモノ', '織物']},
        'Tweed': {'any': ['tweed', 'ついーど', 'ツイード']},
        'Velvet': { 'any': [ 'velvet', ' samt ', 'veludo', 'べるべっと',
                          'ベルベット'],
                 'not': [ 'faux', 'bracelet', 'velvet mirror',
                          'うでわ', 'ウデワ', '腕輪', 'びろーどかがみ', 'ビロードカガミ',
                          'ビロード鏡', 'フェイク']},
        'Viscose': { 'any': [ 'viscose', 'viskose', 'rayon', 'びすこーす',
                           'ビスコース']},
        'Wool': { 'any': [ 'wool', 'flanel', ' lã ', 'ようひ', 'ヨウヒ',
                        '羊毛', 'ウール']}
    }
}

g_material_layers['Jewellery'] = {
    'materials': {
        'Acetate': {'any': [' acetate', 'acetato', 'あせてーと', 'アセテート']},
        'Acrylic': { 'any': [ ' acrylic', 'acrílico', 'acrilico',
                           'あくりる', 'アクリル']},
        'Brass': { 'any': [ ' brass ', ' latão ', 'しんちゅう', 'シンチュウ',
                         '真鍮']},
        'Copper': {'any': [' copper ', 'cobre', '銅']},
        'Denimite': {'any': ['denimite']},
        'Gold': {'any': ['gold', 'ouro', 'ゴールド']},
        'Pearl': {'any': [' pearl ', 'pérola', 'パール']},
        'Resin': {'any': [' resin ', ' resina ', 'じゅし', 'ジュシ', '樹脂']},
        'Ruby': {'any': ['ruby', 'pérola', 'ルビー']},
        'Stainless Steel': { 'all': [ 'stainless steel',
                                   'aço inoxidável']},
        'Sterling Silver': { 'all': [ 'sterling', 'silver', 'ぎん', 'ギン',
                                   '銀', 'ぽんど', 'ポンド'],
                          'not': ['silver look']},
        'Zinc': {'any': [' zinc ', 'zinco', '亜鉛']}
    }
}
