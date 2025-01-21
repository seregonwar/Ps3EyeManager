#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <dshow.h>
#include <strmif.h>
#include <amvideo.h>
#include <dvdmedia.h>
#include <initguid.h>
#include <memory>
#include <mutex>

#ifdef _WIN64
#define DECLARE_PTR(type, ptr, expr) type* ptr = (type*)(expr);
#else
#define DECLARE_PTR(type, ptr, expr) type* ptr = (type*)(expr);
#endif

// Definizione di CCritSec
class CCritSec {
    CRITICAL_SECTION m_CritSec;
public:
    CCritSec() { InitializeCriticalSection(&m_CritSec); }
    ~CCritSec() { DeleteCriticalSection(&m_CritSec); }
    void Lock() { EnterCriticalSection(&m_CritSec); }
    void Unlock() { LeaveCriticalSection(&m_CritSec); }
};

// Helper class for automatic locking
class CAutoLock {
    CCritSec* m_pLock;
public:
    CAutoLock(CCritSec* pLock) : m_pLock(pLock) { m_pLock->Lock(); }
    ~CAutoLock() { m_pLock->Unlock(); }
};

class CMediaType : public AM_MEDIA_TYPE {
public:
    ~CMediaType() {
        if (cbFormat != 0) {
            CoTaskMemFree((PVOID)pbFormat);
            cbFormat = 0;
            pbFormat = NULL;
        }
        if (pUnk != NULL) {
            pUnk->Release();
            pUnk = NULL;
        }
    }
    
    CMediaType() {
        ZeroMemory((PVOID)this, sizeof(*this));
    }
};

// {5C2CD55C-92AD-4999-8666-912C6C45E789}
DEFINE_GUID(CLSID_PS3EyeVirtualCamera, 
0x5c2cd55c, 0x92ad, 0x4999, 0x86, 0x66, 0x91, 0x2c, 0x6c, 0x45, 0xe7, 0x89);

// Dimensioni buffer condiviso
const int SHARED_BUFFER_SIZE = 1920 * 1080 * 3; // Supporta fino a 1080p

// Forward declarations
class PS3EyeVirtualCamera;
class PS3EyeStream;
class CEnumPins;

// Interface for pin enumeration to break circular dependency
class IPinFinder {
public:
    virtual ~IPinFinder() {}
    virtual HRESULT FindPin(LPCWSTR Id, IPin** ppPin) = 0;
};

// CEnumPins declaration
class CEnumPins : public IEnumPins {
public:
    CEnumPins(IPinFinder* pFilter, CEnumPins* pEnum);

    // IUnknown methods
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) override;
    STDMETHODIMP_(ULONG) AddRef() override;
    STDMETHODIMP_(ULONG) Release() override;

    // IEnumPins methods
    STDMETHODIMP Next(ULONG cPins, IPin** ppPins, ULONG* pcFetched) override;
    STDMETHODIMP Skip(ULONG cPins) override;
    STDMETHODIMP Reset() override;
    STDMETHODIMP Clone(IEnumPins** ppEnum) override;

private:
    LONG m_refCount;
    IPinFinder* m_pFilter;
    ULONG m_Position;
};

// PS3EyeStream class definition
class PS3EyeStream : public IPin, public IQualityControl {
public:
    friend class PS3EyeVirtualCamera;
    
    PS3EyeStream(PS3EyeVirtualCamera* pParent);
    ~PS3EyeStream();

    // IUnknown methods
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) override {
        if (ppv == NULL)
            return E_POINTER;

        if (riid == IID_IUnknown || riid == IID_IPin) {
            *ppv = static_cast<IPin*>(this);
        }
        else if (riid == IID_IQualityControl) {
            *ppv = static_cast<IQualityControl*>(this);
        }
        else {
            *ppv = NULL;
            return E_NOINTERFACE;
        }

        AddRef();
        return S_OK;
    }

    STDMETHODIMP_(ULONG) AddRef() override {
        return InterlockedIncrement(&m_refCount);
    }

    STDMETHODIMP_(ULONG) Release() override {
        LONG ref = InterlockedDecrement(&m_refCount);
        if (ref == 0)
            delete this;
        return ref;
    }

    // IPin methods
    STDMETHODIMP Connect(IPin* pReceivePin, const AM_MEDIA_TYPE* pmt) override {
        return S_OK;
    }

    STDMETHODIMP ReceiveConnection(IPin* pConnector, const AM_MEDIA_TYPE* pmt) override {
        return S_OK;
    }

    STDMETHODIMP Disconnect() override {
        return S_OK;
    }

    STDMETHODIMP ConnectedTo(IPin** pPin) override {
        if (pPin == NULL)
            return E_POINTER;
        *pPin = m_pConnected;
        if (m_pConnected)
            m_pConnected->AddRef();
        return S_OK;
    }

    STDMETHODIMP ConnectionMediaType(AM_MEDIA_TYPE* pmt) override {
        if (pmt == NULL)
            return E_POINTER;
        *pmt = m_mt;
        return S_OK;
    }

    STDMETHODIMP QueryPinInfo(PIN_INFO* pInfo) override {
        return S_OK;
    }

    STDMETHODIMP QueryDirection(PIN_DIRECTION* pPinDir) override {
        if (pPinDir == NULL)
            return E_POINTER;
        *pPinDir = PINDIR_OUTPUT;
        return S_OK;
    }

    STDMETHODIMP QueryId(LPWSTR* Id) override {
        return S_OK;
    }

    STDMETHODIMP QueryAccept(const AM_MEDIA_TYPE* pmt) override {
        return S_OK;
    }

    STDMETHODIMP EnumMediaTypes(IEnumMediaTypes** ppEnum) override {
        return S_OK;
    }

    STDMETHODIMP QueryInternalConnections(IPin** apPin, ULONG* nPin) override {
        return S_OK;
    }

    STDMETHODIMP EndOfStream() override {
        return S_OK;
    }

    STDMETHODIMP BeginFlush() override {
        return S_OK;
    }

    STDMETHODIMP EndFlush() override {
        return S_OK;
    }

    STDMETHODIMP NewSegment(REFERENCE_TIME tStart, REFERENCE_TIME tStop, double dRate) override {
        return S_OK;
    }

    // IQualityControl methods
    STDMETHODIMP Notify(IBaseFilter* pSender, Quality q) override {
        return S_OK;
    }

    STDMETHODIMP SetSink(IQualityControl* piqc) override {
        return S_OK;
    }

    // Stream control methods
    HRESULT Active() {
        CAutoLock lock(&m_lock);
        m_bRunning = true;
        return S_OK;
    }

    HRESULT Inactive() {
        CAutoLock lock(&m_lock);
        m_bRunning = false;
        return S_OK;
    }

private:
    LONG m_refCount;
    PS3EyeVirtualCamera* m_pParent;
    IPin* m_pConnected;
    CCritSec m_lock;
    AM_MEDIA_TYPE m_mt;
    VIDEOINFOHEADER m_videoInfo;
    IQualityControl* m_pQSink;
    bool m_bRunning;
};

PS3EyeStream::PS3EyeStream(PS3EyeVirtualCamera* pParent) :
    m_refCount(1),
    m_pParent(pParent),
    m_pConnected(NULL),
    m_pQSink(NULL),
    m_bRunning(false) {
    ZeroMemory(&m_mt, sizeof(AM_MEDIA_TYPE));
    ZeroMemory(&m_videoInfo, sizeof(VIDEOINFOHEADER));
}

PS3EyeStream::~PS3EyeStream() {
    if (m_pConnected)
        m_pConnected->Release();
    if (m_pQSink)
        m_pQSink->Release();
}

// PS3EyeVirtualCamera class definition
class PS3EyeVirtualCamera : public IBaseFilter, public IPinFinder {
public:
    static HRESULT CreateInstance(IBaseFilter** ppFilter) {
        *ppFilter = new PS3EyeVirtualCamera();
        if (*ppFilter == NULL)
            return E_OUTOFMEMORY;
        (*ppFilter)->AddRef();
        return S_OK;
    }

    // IUnknown methods
    STDMETHODIMP QueryInterface(REFIID riid, void** ppv) override {
        if (ppv == NULL)
            return E_POINTER;

        if (riid == IID_IUnknown) {
            *ppv = static_cast<IBaseFilter*>(this);
        }
        else if (riid == IID_IMediaFilter) {
            *ppv = static_cast<IBaseFilter*>(this);
        }
        else if (riid == IID_IBaseFilter) {
            *ppv = static_cast<IBaseFilter*>(this);
        }
        else if (riid == IID_IPersist) {
            *ppv = static_cast<IPersist*>(static_cast<IBaseFilter*>(this));
        }
        else {
            *ppv = NULL;
            return E_NOINTERFACE;
        }

        AddRef();
        return S_OK;
    }

    STDMETHODIMP_(ULONG) AddRef() override {
        return InterlockedIncrement(&m_refCount);
    }

    STDMETHODIMP_(ULONG) Release() override {
        LONG ref = InterlockedDecrement(&m_refCount);
        if (ref == 0)
            delete this;
        return ref;
    }

    // IPersist method (inherited through IBaseFilter)
    STDMETHODIMP GetClassID(CLSID* pClsid) override {
        if (pClsid == NULL)
            return E_POINTER;
        *pClsid = CLSID_PS3EyeVirtualCamera;
        return S_OK;
    }

    // IMediaFilter methods
    STDMETHODIMP Run(REFERENCE_TIME tStart) override {
        CAutoLock lock(&m_lock);
        m_state = State_Running;
        if (m_pStream)
            m_pStream->Active();
        return S_OK;
    }

    STDMETHODIMP Pause() override {
        CAutoLock lock(&m_lock);
        m_state = State_Paused;
        return S_OK;
    }

    STDMETHODIMP Stop() override {
        CAutoLock lock(&m_lock);
        m_state = State_Stopped;
        if (m_pStream)
            m_pStream->Inactive();
        return S_OK;
    }

    STDMETHODIMP GetState(DWORD dwMilliSecsTimeout, FILTER_STATE* pState) override {
        if (pState == NULL)
            return E_POINTER;
        CAutoLock lock(&m_lock);
        *pState = m_state;
        return S_OK;
    }

    STDMETHODIMP SetSyncSource(IReferenceClock* pClock) override {
        CAutoLock lock(&m_lock);
        if (m_pClock)
            m_pClock->Release();
        m_pClock = pClock;
        if (m_pClock)
            m_pClock->AddRef();
        return S_OK;
    }

    STDMETHODIMP GetSyncSource(IReferenceClock** ppClock) override {
        if (ppClock == NULL)
            return E_POINTER;
        CAutoLock lock(&m_lock);
        *ppClock = m_pClock;
        if (m_pClock)
            m_pClock->AddRef();
        return S_OK;
    }

    // IBaseFilter methods
    STDMETHODIMP EnumPins(IEnumPins** ppEnum) override {
        if (ppEnum == NULL)
            return E_POINTER;
        
        // Create a new enumerator
        *ppEnum = new CEnumPins(this, NULL);
        if (*ppEnum == NULL)
            return E_OUTOFMEMORY;
            
        return S_OK;
    }

    STDMETHODIMP FindPin(LPCWSTR Id, IPin** ppPin) override {
        if (ppPin == NULL)
            return E_POINTER;
        
        // We only have one output pin
        if (lstrcmpW(Id, L"Output") == 0) {
            *ppPin = m_pStream;
            if (m_pStream)
                m_pStream->AddRef();
            return S_OK;
        }
        
        *ppPin = NULL;
        return VFW_E_NOT_FOUND;
    }

    STDMETHODIMP QueryFilterInfo(FILTER_INFO* pInfo) override {
        if (pInfo == NULL)
            return E_POINTER;
        
        CAutoLock lock(&m_lock);
        lstrcpyW(pInfo->achName, m_filterName);
        pInfo->pGraph = m_pGraph;
        if (m_pGraph)
            m_pGraph->AddRef();
            
        return S_OK;
    }

    STDMETHODIMP JoinFilterGraph(IFilterGraph* pGraph, LPCWSTR pName) override {
        CAutoLock lock(&m_lock);
        m_pGraph = pGraph;
        if (pName)
            lstrcpyW(m_filterName, pName);
        return S_OK;
    }

    STDMETHODIMP QueryVendorInfo(LPWSTR* pVendorInfo) override {
        if (pVendorInfo == NULL)
            return E_POINTER;
        *pVendorInfo = NULL;
        return E_NOTIMPL;
    }

private:
    PS3EyeVirtualCamera() : 
        m_refCount(1),
        m_pGraph(NULL),
        m_state(State_Stopped),
        m_pClock(NULL),
        m_pStream(NULL) {
        m_filterName[0] = L'\0';
        m_pStream = new PS3EyeStream(this);
    }

    ~PS3EyeVirtualCamera() {
        if (m_pClock)
            m_pClock->Release();
        if (m_pStream)
            m_pStream->Release();
    }

    LONG m_refCount;
    IFilterGraph* m_pGraph;
    FILTER_STATE m_state;
    CCritSec m_lock;
    IReferenceClock* m_pClock;
    PS3EyeStream* m_pStream;
    WCHAR m_filterName[128];
};

// CEnumPins implementation
CEnumPins::CEnumPins(IPinFinder* pFilter, CEnumPins* pEnum) :
    m_refCount(1),
    m_pFilter(pFilter),
    m_Position(0) {
    if (pEnum)
        m_Position = pEnum->m_Position;
}

STDMETHODIMP CEnumPins::QueryInterface(REFIID riid, void** ppv) {
    if (ppv == NULL)
        return E_POINTER;

    if (riid == IID_IUnknown || riid == IID_IEnumPins) {
        *ppv = static_cast<IEnumPins*>(this);
        AddRef();
        return S_OK;
    }

    *ppv = NULL;
    return E_NOINTERFACE;
}

STDMETHODIMP_(ULONG) CEnumPins::AddRef() {
    return InterlockedIncrement(&m_refCount);
}

STDMETHODIMP_(ULONG) CEnumPins::Release() {
    LONG ref = InterlockedDecrement(&m_refCount);
    if (ref == 0)
        delete this;
    return ref;
}

STDMETHODIMP CEnumPins::Next(ULONG cPins, IPin** ppPins, ULONG* pcFetched) {
    if (ppPins == NULL)
        return E_POINTER;

    if (pcFetched)
        *pcFetched = 0;
    else if (cPins > 1)
        return E_INVALIDARG;

    ULONG cFetched = 0;
    while (cFetched < cPins && m_Position < 1) {
        IPin* pPin;
        HRESULT hr = m_pFilter->FindPin(L"Output", &pPin);
        if (FAILED(hr))
            break;

        ppPins[cFetched++] = pPin;
        m_Position++;
    }

    if (pcFetched)
        *pcFetched = cFetched;

    return (cFetched == cPins) ? S_OK : S_FALSE;
}

STDMETHODIMP CEnumPins::Skip(ULONG cPins) {
    m_Position += cPins;
    return (m_Position <= 1) ? S_OK : S_FALSE;
}

STDMETHODIMP CEnumPins::Reset() {
    m_Position = 0;
    return S_OK;
}

STDMETHODIMP CEnumPins::Clone(IEnumPins** ppEnum) {
    if (ppEnum == NULL)
        return E_POINTER;

    *ppEnum = new CEnumPins(m_pFilter, this);
    if (*ppEnum == NULL)
        return E_OUTOFMEMORY;

    return S_OK;
}

// Factory function
STDAPI DllGetClassObject(REFCLSID rclsid, REFIID riid, void** ppv)
{
    if (rclsid != CLSID_PS3EyeVirtualCamera)
        return CLASS_E_CLASSNOTAVAILABLE;
        
    IBaseFilter* pFilter;
    HRESULT hr = PS3EyeVirtualCamera::CreateInstance(&pFilter);
    if (FAILED(hr))
        return hr;
        
    hr = pFilter->QueryInterface(riid, ppv);
    pFilter->Release();
    return hr;
}

STDAPI DllRegisterServer()
{
    // Registra il filtro DirectShow
    HKEY hKey;
    DWORD dw;
    WCHAR szCLSID[50];
    WCHAR szFile[512];
    WCHAR szKey[256];
    
    StringFromGUID2(CLSID_PS3EyeVirtualCamera, szCLSID, 50);
    GetModuleFileNameW(NULL, szFile, 512);
    
    // Crea le chiavi di registro
    wsprintfW(szKey, L"CLSID\\%s", szCLSID);
    RegCreateKeyExW(HKEY_CLASSES_ROOT, szKey, 0, NULL, REG_OPTION_NON_VOLATILE,
                  KEY_ALL_ACCESS, NULL, &hKey, &dw);
    RegSetValueExW(hKey, NULL, 0, REG_SZ, (BYTE*)L"PS3 Eye Virtual Camera",
                 sizeof(L"PS3 Eye Virtual Camera"));
    RegCloseKey(hKey);
    
    wsprintfW(szKey, L"CLSID\\%s\\InprocServer32", szCLSID);
    RegCreateKeyExW(HKEY_CLASSES_ROOT, szKey, 0, NULL, REG_OPTION_NON_VOLATILE,
                  KEY_ALL_ACCESS, NULL, &hKey, &dw);
    RegSetValueExW(hKey, NULL, 0, REG_SZ, (BYTE*)szFile, (lstrlenW(szFile) + 1) * sizeof(WCHAR));
    RegSetValueExW(hKey, L"ThreadingModel", 0, REG_SZ, (BYTE*)L"Both",
                 sizeof(L"Both"));
    RegCloseKey(hKey);
    
    return S_OK;
}

STDAPI DllUnregisterServer()
{
    WCHAR szCLSID[50];
    StringFromGUID2(CLSID_PS3EyeVirtualCamera, szCLSID, 50);
    
    WCHAR szKey[256];
    wsprintfW(szKey, L"CLSID\\%s", szCLSID);
    RegDeleteKeyW(HKEY_CLASSES_ROOT, szKey);
    
    return S_OK;
}

STDAPI DllCanUnloadNow()
{
    return S_OK;
}
