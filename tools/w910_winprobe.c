#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <setupapi.h>
#include <hidsdi.h>
#include <hidpi.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define REPORT_ID 0x06
#define REPORT_SIZE 41
#define MAX_DATA 32
#define MACRO_SIZE 512

typedef struct {
    const char *name;
    uint16_t index;
} control_t;

static const control_t main_controls[] = {
    {"key_esc", 0}, {"key_x", 1}, {"rgb_light_switch", 2},
    {"key_b", 8}, {"key_v", 9}, {"mode_switch_press", 10},
    {"key_c", 16}, {"key_enter", 17}, {"mode_switch_up", 18},
    {"key_d", 24}, {"key_left_shift", 25}, {"mode_switch_down", 26},
    {"key_e", 32}, {"key_k", 33}, {"mode_switch_left", 34},
    {"key_tab", 40}, {"key_r", 41}, {"mode_switch_right", 42},
};

static int is_w910(USHORT vid, USHORT pid) {
    return (vid == 0x36a4 || vid == 0xb6a4) &&
           (pid == 0x4100 || pid == 0x4101);
}

static void hex(const BYTE *data, size_t length) {
    size_t i;
    for (i = 0; i < length; ++i) printf("%02X", data[i]);
}

static HANDLE open_vendor_collection(void) {
    GUID guid;
    HDEVINFO set;
    SP_DEVICE_INTERFACE_DATA iface;
    DWORD index;

    HidD_GetHidGuid(&guid);
    set = SetupDiGetClassDevsA(&guid, NULL, NULL,
                               DIGCF_PRESENT | DIGCF_DEVICEINTERFACE);
    if (set == INVALID_HANDLE_VALUE) return INVALID_HANDLE_VALUE;

    iface.cbSize = sizeof(iface);
    for (index = 0; SetupDiEnumDeviceInterfaces(set, NULL, &guid, index, &iface);
         ++index) {
        DWORD required = 0;
        PSP_DEVICE_INTERFACE_DETAIL_DATA_A detail;
        HANDLE handle;
        HIDD_ATTRIBUTES attr;
        PHIDP_PREPARSED_DATA preparsed = NULL;
        HIDP_CAPS caps;
        int match = 0;

        SetupDiGetDeviceInterfaceDetailA(set, &iface, NULL, 0, &required, NULL);
        detail = (PSP_DEVICE_INTERFACE_DETAIL_DATA_A)malloc(required);
        if (!detail) continue;
        detail->cbSize = sizeof(*detail);
        if (!SetupDiGetDeviceInterfaceDetailA(set, &iface, detail, required,
                                               NULL, NULL)) {
            free(detail);
            continue;
        }
        handle = CreateFileA(detail->DevicePath, GENERIC_READ | GENERIC_WRITE,
                             FILE_SHARE_READ | FILE_SHARE_WRITE, NULL,
                             OPEN_EXISTING, 0, NULL);
        free(detail);
        if (handle == INVALID_HANDLE_VALUE) continue;

        memset(&attr, 0, sizeof(attr));
        attr.Size = sizeof(attr);
        memset(&caps, 0, sizeof(caps));
        if (HidD_GetAttributes(handle, &attr) && is_w910(attr.VendorID, attr.ProductID) &&
            HidD_GetPreparsedData(handle, &preparsed)) {
            match = HidP_GetCaps(preparsed, &caps) == HIDP_STATUS_SUCCESS &&
                    caps.UsagePage == 0xFF01 && caps.Usage == 0x0001 &&
                    caps.FeatureReportByteLength == REPORT_SIZE;
            HidD_FreePreparsedData(preparsed);
        }
        if (match) {
            SetupDiDestroyDeviceInfoList(set);
            return handle;
        }
        CloseHandle(handle);
    }
    SetupDiDestroyDeviceInfoList(set);
    return INVALID_HANDLE_VALUE;
}

static int query(HANDLE device, BYTE *sequence, BYTE command, BYTE selector,
                 WORD address, BYTE length, BYTE response[REPORT_SIZE]) {
    BYTE request[REPORT_SIZE];
    int attempt;
    if (command < 0x80 || length > MAX_DATA) return 0;
    memset(request, 0, sizeof(request));
    request[0] = REPORT_ID;
    request[1] = 0;
    request[2] = 1;
    request[3] = command;
    request[4] = ++*sequence;
    request[5] = selector;
    request[6] = (BYTE)address;
    request[7] = (BYTE)(address >> 8);
    request[8] = length;
    if (!HidD_SetFeature(device, request, sizeof(request))) return 0;
    for (attempt = 0; attempt < 5; ++attempt) {
        Sleep(20);
        memset(response, 0, REPORT_SIZE);
        response[0] = REPORT_ID;
        if (!HidD_GetFeature(device, response, REPORT_SIZE)) return 0;
        if (response[8] != 0) return 1;
    }
    return 0;
}

static int print_query(HANDLE device, BYTE *sequence, const char *name,
                       BYTE command, BYTE selector, WORD address, BYTE length) {
    BYTE response[REPORT_SIZE];
    if (!query(device, sequence, command, selector, address, length, response)) {
        fprintf(stderr, "%s: query failed, winerr=%lu\n", name, GetLastError());
        return 0;
    }
    printf("%-22s cmd=%02X sel=%u addr=%04X len=%u data=", name, command,
           selector, address, response[8]);
    hex(response + 9, response[8]);
    putchar('\n');
    return 1;
}

static int dump_device(HANDLE device) {
    BYTE seq = 0;
    BYTE response[REPORT_SIZE];
    size_t i;
    int ok = 1;
    ok &= print_query(device, &seq, "status", 0x81, 0, 0, 3);
    ok &= print_query(device, &seq, "generation_tokens", 0x82, 1, 0, 8);
    ok &= print_query(device, &seq, "onboard_slot", 0x82, 2, 0, 1);
    ok &= print_query(device, &seq, "sleep_seconds", 0x82, 3, 0, 2);
    ok &= print_query(device, &seq, "powerdown_seconds", 0x82, 4, 0, 2);
    for (BYTE layer = 0; layer < 2; ++layer) {
        for (i = 0; i < sizeof(main_controls) / sizeof(main_controls[0]); ++i) {
            char label[64];
            _snprintf(label, sizeof(label), "%s/%s",
                      layer ? "fn" : "normal", main_controls[i].name);
            ok &= print_query(device, &seq, label, 0x84, layer,
                              main_controls[i].index * 4, 4);
        }
        ok &= print_query(device, &seq,
                          layer ? "fn/scroll_up" : "normal/scroll_up",
                          0x85, layer, 0, 4);
        ok &= print_query(device, &seq,
                          layer ? "fn/scroll_down" : "normal/scroll_down",
                          0x85, layer, 4, 4);
    }
    if (query(device, &seq, 0x89, 0, 0, 25, response)) {
        printf("%-22s cmd=89 sel=0 addr=0000 len=%u data=", "lighting/header",
               response[8]);
        hex(response + 9, response[8]);
        putchar('\n');
        if ((response[9] & 0x3F) >= 1 && (response[9] & 0x3F) <= 8)
            ok &= print_query(device, &seq, "lighting/detail", 0x89, 0,
                              (response[9] & 0x3F) * 25, 25);
    } else {
        ok = 0;
    }
    return ok ? 0 : 1;
}

static int dump_macro(HANDLE device, BYTE slot) {
    BYTE seq = 0, response[REPORT_SIZE], stream[MACRO_SIZE];
    size_t total, address;
    if (!query(device, &seq, 0x88, slot, 0, MAX_DATA, response)) return 1;
    memcpy(stream, response + 9, MAX_DATA);
    total = 4 + stream[2] + ((size_t)stream[3] << 8);
    if (total > sizeof(stream)) return 1;
    for (address = MAX_DATA; address < total; address += MAX_DATA) {
        BYTE length = (BYTE)((total - address) > MAX_DATA ? MAX_DATA : total - address);
        if (!query(device, &seq, 0x88, slot, (WORD)address, length, response)) return 1;
        memcpy(stream + address, response + 9, length);
    }
    printf("slot=%u repeat=%u payload=%u raw=", slot,
           stream[0] | ((unsigned)stream[1] << 8),
           stream[2] | ((unsigned)stream[3] << 8));
    hex(stream, total);
    putchar('\n');
    return 0;
}

int main(int argc, char **argv) {
    HANDLE device = open_vendor_collection();
    int result;
    if (device == INVALID_HANDLE_VALUE) {
        fprintf(stderr, "W910 FF01:0001 collection not found/openable, winerr=%lu\n",
                GetLastError());
        return 1;
    }
    if (argc == 2 && strcmp(argv[1], "dump") == 0) {
        result = dump_device(device);
    } else if (argc == 3 && strcmp(argv[1], "dump-macro") == 0) {
        char *end = NULL;
        unsigned long slot = strtoul(argv[2], &end, 0);
        if (!argv[2][0] || *end || slot > 255) result = 2;
        else result = dump_macro(device, (BYTE)slot);
    } else {
        fprintf(stderr, "usage: %s dump | dump-macro SLOT\n", argv[0]);
        result = 2;
    }
    CloseHandle(device);
    return result;
}
