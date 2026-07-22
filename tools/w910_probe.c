#include <hidapi.h>
#ifdef __APPLE__
#include <hidapi_darwin.h>
#endif

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define W910_REPORT_ID 0x06
#define W910_REPORT_SIZE 41
#define W910_DATA_SIZE 32
#define W910_MACRO_SIZE 512

static int is_w910(uint16_t vid, uint16_t pid) {
    return (vid == 0x36a4 || vid == 0xb6a4) &&
           (pid == 0x4100 || pid == 0x4101);
}

static int is_known_read_command(uint8_t command) {
    switch (command) {
    case 0x81:
    case 0x82:
    case 0x83:
    case 0x84:
    case 0x85:
    case 0x86:
    case 0x87:
    case 0x88:
    case 0x89:
    case 0x8a:
    case 0xf0:
    case 0xf1:
        return 1;
    default:
        return 0;
    }
}

static void print_wide(const wchar_t *value) {
    if (value == NULL) {
        fputs("(null)", stdout);
        return;
    }
    while (*value != L'\0') {
        wchar_t ch = *value++;
        putchar((ch >= 0x20 && ch <= 0x7e) ? (char)ch : '?');
    }
}

static int list_devices(void) {
    struct hid_device_info *devices = hid_enumerate(0, 0);
    struct hid_device_info *item = devices;
    int count = 0;

    while (item != NULL) {
        if (!is_w910(item->vendor_id, item->product_id)) {
            item = item->next;
            continue;
        }
        printf("[%d]\n", count);
        printf("  path: %s\n", item->path);
        printf("  vid:pid: %04hx:%04hx\n", item->vendor_id, item->product_id);
        printf("  release: %04hx\n", item->release_number);
        printf("  interface: %d\n", item->interface_number);
        printf("  usage: %04hx:%04hx\n", item->usage_page, item->usage);
        printf("  manufacturer: ");
        print_wide(item->manufacturer_string);
        putchar('\n');
        printf("  product: ");
        print_wide(item->product_string);
        putchar('\n');
        printf("  serial: ");
        print_wide(item->serial_number);
        putchar('\n');
#if HID_API_VERSION >= HID_API_MAKE_VERSION(0, 13, 0)
        printf("  bus_type: %d\n", item->bus_type);
#endif
        item = item->next;
        count++;
    }

    hid_free_enumeration(devices);
    return count == 0 ? 1 : 0;
}

static char *find_vendor_path(void) {
    struct hid_device_info *devices = hid_enumerate(0, 0);
    struct hid_device_info *item = devices;
    char *path = NULL;

    while (item != NULL) {
        if (is_w910(item->vendor_id, item->product_id) &&
            item->usage_page == 0xff01 && item->usage == 0x0001) {
            size_t size = strlen(item->path) + 1;
            path = malloc(size);
            if (path != NULL) {
                memcpy(path, item->path, size);
            }
            break;
        }
        item = item->next;
    }
    hid_free_enumeration(devices);
    return path;
}

static hid_device *open_device(void) {
    char *path = find_vendor_path();
    hid_device *device;

    if (path == NULL) {
        fputs("W910 FF01:0001 HID collection not found\n", stderr);
        return NULL;
    }
    device = hid_open_path(path);
    free(path);
    if (device == NULL) {
        fwprintf(stderr, L"hid_open_path failed: %ls\n", hid_error(NULL));
    }
    return device;
}

static void print_hex(const uint8_t *data, size_t size) {
    for (size_t i = 0; i < size; i++) {
        printf("%02x", data[i]);
    }
    putchar('\n');
}

static int query_raw(hid_device *device, uint8_t *sequence, uint8_t command,
                     uint8_t selector, uint16_t address, uint8_t length,
                     uint8_t response[W910_REPORT_SIZE], int verbose) {
    uint8_t request[W910_REPORT_SIZE] = {0};
    const struct timespec delay = {.tv_sec = 0, .tv_nsec = 20 * 1000 * 1000};
    int result;

    request[0] = W910_REPORT_ID;
    request[1] = 0x00;
    request[2] = 0x01;
    request[3] = command;
    request[4] = ++*sequence;
    request[5] = selector;
    request[6] = (uint8_t)(address & 0xff);
    request[7] = (uint8_t)(address >> 8);
    request[8] = length;

    if (verbose) {
        fputs("request:  ", stdout);
        print_hex(request, sizeof(request));
    }
    result = hid_send_feature_report(device, request, sizeof(request));
    if (result < 0) {
        fwprintf(stderr, L"hid_send_feature_report failed: %ls\n",
                 hid_error(device));
        return 0;
    }
    if (verbose) {
        printf("set-size: %d\n", result);
    }

    for (int attempt = 1; attempt <= 5; attempt++) {
        nanosleep(&delay, NULL);
        memset(response, 0, W910_REPORT_SIZE);
        response[0] = W910_REPORT_ID;
        result = hid_get_feature_report(device, response, W910_REPORT_SIZE);
        if (result < 0) {
            fwprintf(stderr, L"hid_get_feature_report failed: %ls\n",
                     hid_error(device));
            return 0;
        }
        if (verbose) {
            printf("response[%d,%d]: ", attempt, result);
            print_hex(response, W910_REPORT_SIZE);
        }
        if (result >= 9 && response[8] != 0) {
            return 1;
        }
    }
    return 0;
}

static void print_record(const char *label, uint8_t selector, uint16_t address,
                         const uint8_t response[W910_REPORT_SIZE]) {
    printf("%-18s sel=%u addr=%04x len=%u data=", label, selector, address,
           response[8]);
    print_hex(response + 9, response[8] <= W910_DATA_SIZE ? response[8] : 0);
}

static int query_device(uint8_t command, uint8_t selector, uint16_t address,
                        uint8_t length) {
    uint8_t response[W910_REPORT_SIZE];
    uint8_t sequence = 0;
    hid_device *device = open_device();
    int ok;

    if (device == NULL) {
        return 1;
    }
    ok = query_raw(device, &sequence, command, selector, address, length,
                   response, 1);
    hid_close(device);
    return ok ? 0 : 1;
}

static int dump_one(hid_device *device, uint8_t *sequence, const char *label,
                    uint8_t command, uint8_t selector, uint16_t address,
                    uint8_t length) {
    uint8_t response[W910_REPORT_SIZE];

    if (!query_raw(device, sequence, command, selector, address, length,
                   response, 0)) {
        fprintf(stderr, "%s sel=%u addr=%04x: no response\n", label, selector,
                address);
        return 0;
    }
    print_record(label, selector, address, response);
    return 1;
}

static const struct {
    const char *name;
    uint16_t index;
} main_controls[] = {
    {"key_esc", 0}, {"key_x", 1}, {"rgb_light_switch", 2},
    {"key_b", 8}, {"key_v", 9}, {"mode_switch_press", 10},
    {"key_c", 16}, {"key_enter", 17}, {"mode_switch_up", 18},
    {"key_d", 24}, {"key_left_shift", 25}, {"mode_switch_down", 26},
    {"key_e", 32}, {"key_k", 33}, {"mode_switch_left", 34},
    {"key_tab", 40}, {"key_r", 41}, {"mode_switch_right", 42},
};

static int dump_device(void) {
    hid_device *device = open_device();
    uint8_t sequence = 0;
    int failures = 0;

    if (device == NULL) {
        return 1;
    }
    failures += !dump_one(device, &sequence, "status", 0x81, 0, 0, 3);
    failures += !dump_one(device, &sequence, "profile-sync-ids", 0x82, 1, 0, 8);
    failures += !dump_one(device, &sequence, "selected-profile", 0x82, 2, 0, 1);
    failures += !dump_one(device, &sequence, "sleep-seconds", 0x82, 3, 0, 2);
    failures += !dump_one(device, &sequence, "powerdown-seconds", 0x82, 4, 0, 2);
    failures += !dump_one(device, &sequence, "global-5", 0x82, 5, 0, 1);
    failures += !dump_one(device, &sequence, "global-6", 0x82, 6, 0, 1);
    failures += !dump_one(device, &sequence, "charge-count", 0x82, 7, 0, 1);
    failures += !dump_one(device, &sequence, "report-rate", 0x83, 0, 0, 1);
    failures += !dump_one(device, &sequence, "firmware-version", 0xf0, 1, 0, 8);
    failures += !dump_one(device, &sequence, "firmware-custom", 0xf0, 2, 0, 16);
    failures += !dump_one(device, &sequence, "dongle-firmware", 0xf1, 1, 0, 8);

    for (uint8_t layer = 0; layer < 2; layer++) {
        for (size_t key = 0; key < sizeof(main_controls) / sizeof(main_controls[0]); key++) {
            char label[48];
            snprintf(label, sizeof(label), "%s/%s", layer ? "fn" : "normal",
                     main_controls[key].name);
            failures += !dump_one(device, &sequence, label, 0x84, layer,
                                  (uint16_t)(main_controls[key].index * 4), 4);
        }
        for (uint16_t wheel = 0; wheel < 2; wheel++) {
            char label[48];
            snprintf(label, sizeof(label), "%s/scroll-%s", layer ? "fn" : "normal",
                     wheel ? "down" : "up");
            failures += !dump_one(device, &sequence, label, 0x85, layer,
                                  (uint16_t)(wheel * 4), 4);
        }
    }
    failures += !dump_one(device, &sequence, "led-header", 0x89, 0, 0, 25);
    hid_close(device);
    return failures == 0 ? 0 : 1;
}

static int dump_macro(uint8_t slot) {
    hid_device *device = open_device();
    uint8_t response[W910_REPORT_SIZE];
    uint8_t macro[W910_MACRO_SIZE] = {0};
    uint8_t sequence = 0;
    size_t total;

    if (device == NULL) {
        return 1;
    }
    if (!query_raw(device, &sequence, 0x88, slot, 0, W910_DATA_SIZE,
                   response, 0)) {
        fprintf(stderr, "macro slot %u: no response\n", slot);
        hid_close(device);
        return 1;
    }
    memcpy(macro, response + 9, W910_DATA_SIZE);
    total = (size_t)macro[2] | ((size_t)macro[3] << 8);
    total += 4;
    if (total > W910_MACRO_SIZE) {
        fprintf(stderr, "macro slot %u: invalid size %zu\n", slot, total);
        hid_close(device);
        return 1;
    }
    for (size_t address = W910_DATA_SIZE; address < total;
         address += W910_DATA_SIZE) {
        uint8_t length = (uint8_t)(total - address);
        if (length > W910_DATA_SIZE) {
            length = W910_DATA_SIZE;
        }
        if (!query_raw(device, &sequence, 0x88, slot, (uint16_t)address,
                       length, response, 0)) {
            fprintf(stderr, "macro slot %u offset %zu: no response\n", slot,
                    address);
            hid_close(device);
            return 1;
        }
        memcpy(macro + address, response + 9, length);
    }
    hid_close(device);
    printf("slot=%u repeat=%u payload=%zu raw=", slot,
           (unsigned)macro[0] | ((unsigned)macro[1] << 8), total - 4);
    print_hex(macro, total);
    return 0;
}

static int parse_u32(const char *text, uint32_t maximum, uint32_t *value) {
    char *end = NULL;
    unsigned long parsed = strtoul(text, &end, 0);
    if (text[0] == '\0' || end == NULL || *end != '\0' || parsed > maximum) {
        return 0;
    }
    *value = (uint32_t)parsed;
    return 1;
}

int main(int argc, char **argv) {
    int result;

    if (argc < 2) {
        fprintf(stderr,
                "usage: %s list\n"
                "       %s dump\n"
                "       %s dump-macro SLOT\n"
                "       %s query COMMAND SELECTOR ADDRESS LENGTH\n",
                argv[0], argv[0], argv[0], argv[0]);
        return 2;
    }
#ifdef __APPLE__
    hid_darwin_set_open_exclusive(0);
#endif
    if (hid_init() != 0) {
        fputs("hid_init failed\n", stderr);
        return 1;
    }
    if (argc == 2 && strcmp(argv[1], "list") == 0) {
        result = list_devices();
    } else if (argc == 2 && strcmp(argv[1], "dump") == 0) {
        result = dump_device();
    } else if (argc == 3 && strcmp(argv[1], "dump-macro") == 0) {
        uint32_t slot;
        if (!parse_u32(argv[2], 0xff, &slot)) {
            fputs("invalid macro slot\n", stderr);
            result = 2;
        } else {
            result = dump_macro((uint8_t)slot);
        }
    } else if (argc == 6 && strcmp(argv[1], "query") == 0) {
        uint32_t command, selector, address, length;
        if (!parse_u32(argv[2], 0xff, &command) ||
            !is_known_read_command((uint8_t)command) ||
            !parse_u32(argv[3], 0xff, &selector) ||
            !parse_u32(argv[4], 0xffff, &address) ||
            !parse_u32(argv[5], W910_DATA_SIZE, &length)) {
            fputs("invalid read-only query (unknown read command or length > 32)\n",
                  stderr);
            result = 2;
        } else {
            result = query_device((uint8_t)command, (uint8_t)selector,
                                  (uint16_t)address, (uint8_t)length);
        }
    } else {
        fputs("invalid arguments\n", stderr);
        result = 2;
    }
    hid_exit();
    return result;
}
