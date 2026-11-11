import hashlib,io,json,zipfile

import pytest
from PIL import Image

import workbuddy_pet.material_download as downloads
from workbuddy_pet.materials import MaterialLibrary,MaterialError


def catalog_fixture(tmp_path,monkeypatch):
    picture=io.BytesIO();Image.new('RGBA',(16,16),'blue').save(picture,format='PNG')
    stream=io.BytesIO()
    with zipfile.ZipFile(stream,'w') as z:
        z.writestr('idle.png',picture.getvalue())
        z.writestr('manifest.json',json.dumps({'schema':1,'id':'synthetic','name':'test','author':'test',
            'license':'CC0-1.0','version':'1','quality':'light','actions':{'idle':{'file':'idle.png'}}}))
    data=stream.getvalue()
    spec={'name':'test.zip','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
          'url':'https://github.com/Yujianrx/workbuddy-desktop-pet/releases/download/v0.3.1/test.zip'}
    path=tmp_path/'catalog.json'
    def save():path.write_text(json.dumps({'schema':1,'release':'v0.3.1','packs':{'light':spec}}))
    save();monkeypatch.setattr(downloads,'CATALOG_PATH',path)
    calls=[]
    def fetch(url,**kwargs):calls.append(url);return io.BytesIO(data)
    monkeypatch.setattr(downloads,'urlopen',fetch)
    return spec,save,calls


def test_shipped_catalog_matches_release_and_has_no_remote_packs(tmp_path):
    from workbuddy_pet import __version__
    from workbuddy_pet.update import REPOSITORY
    catalog=json.loads(downloads.CATALOG_PATH.read_text(encoding='utf-8'))
    assert catalog=={'schema':1,'release':'v'+__version__,'packs':{}}
    assert REPOSITORY=='Yujianrx/workbuddy-desktop-pet'
    with pytest.raises(MaterialError,match='下载清单无效'):
        downloads.download_default('hd',MaterialLibrary(tmp_path/'library'))


def test_release_download_keeps_digest_and_import_validation(tmp_path,monkeypatch):
    spec,save,calls=catalog_fixture(tmp_path,monkeypatch)
    pack=downloads.download_default('light',MaterialLibrary(tmp_path/'library'))
    assert pack.quality=='light' and calls==[spec['url']]


@pytest.mark.parametrize('change',[{'url':'https://github.com/other/project/releases/download/v0.3.1/test.zip'},
                                  {'name':'../test.zip'}, {'bytes':True}, {'sha256':'bad'}])
def test_invalid_catalog_is_rejected_before_network(tmp_path,monkeypatch,change):
    spec,save,calls=catalog_fixture(tmp_path,monkeypatch);spec.update(change);save()
    with pytest.raises(MaterialError):downloads.download_default('light',MaterialLibrary(tmp_path/'library'))
    assert not calls


def test_digest_mismatch_does_not_install(tmp_path,monkeypatch):
    spec,save,calls=catalog_fixture(tmp_path,monkeypatch);spec['sha256']='0'*64;save()
    library=MaterialLibrary(tmp_path/'library')
    with pytest.raises(MaterialError):downloads.download_default('light',library)
    assert not library.list_packs()
