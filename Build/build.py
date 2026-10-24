#!/usr/bin/env python3
"""Build the single-source Super Ninja Boyz org/db patch; no assembler dependency.

Identity and output size come from the authoritative ASM. The no-write research
baseline is byte-identical. Changed 1 MiB builds receive a fresh LoROM checksum.
Version0.7 adds the expanded ROM and rewritten relocated opening through03AK.
The archived version0.1 source still builds the 1 MiB research baseline.
"""
from pathlib import Path
import argparse
import hashlib
import re
import zlib

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "Build" / "Janky_Ninja_Boy_v0.38.asm"
DEFAULT_BASE = ROOT / "Build" / "Super Ninja Boy (USA).sfc"


def metadata(text, key):
    matches = re.findall(rf"^; @{key}\s+(\S+)\s*$", text, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one ASM @{key} declaration")
    return matches[0]


def cpu_to_pc(address, size):
    bank, offset = address >> 16, address & 0xFFFF
    if size not in (0x100000,0x200000,0x400000):
        raise ValueError('Unsupported LoROM size')
    last_bank=size//0x8000-1
    if offset < 0x8000 or not (0 <= bank <= last_bank or 0x80 <= bank <= 0x80+last_bank):
        raise ValueError(f"Not a supported ROM window: ${address:06X}")
    if bank in (0x7e,0x7f):
        raise ValueError(f"Address is work RAM, not ROM: ${address:06X}")
    pc = (bank & 0x7F) * 0x8000 + offset - 0x8000
    if pc >= size:
        raise ValueError(f"Address beyond ROM: ${address:06X}")
    return pc


def byte_list(value):
    if not re.fullmatch(r"\$[0-9a-fA-F]{2}(?:\s*,\s*\$[0-9a-fA-F]{2})*", value):
        raise ValueError(f"Expected comma-separated $XX bytes: {value}")
    return bytes(int(token.strip()[1:], 16) for token in value.split(","))


def sram_recipe(text, speed):
    """Resolve inline common SRAM records plus optional broader FastROM records."""
    if speed not in ('slow','fast'):raise ValueError('Unknown SRAM speed variant')
    expects=re.findall(r'^; @sram_expect \$([A-F0-9]{6}) (.+)$',text,re.M)
    records=re.findall(r'^; @sram_db \$([A-F0-9]{6}) (.+)$',text,re.M)
    if not records or len(dict(records))!=len(records) or len(dict(expects))!=len(expects):
        raise ValueError('Missing or duplicate SRAM recipes')
    expected=dict(expects)
    if expected.keys()!=dict(records).keys():raise ValueError('SRAM assertions differ from writes')
    changes={int(a,16):(expected[a],data) for a,data in records}
    if speed=='fast':
        fast=re.findall(r'^; @broad_fastrom \$([A-F0-9]{6}) \$([A-F0-9]{2}) \$([A-F0-9]{2})$',text,re.M)
        if len(fast)!=59:raise ValueError('Expected the accepted59-byte FastROM recipe')
        for a,old,new in fast:
            address=int(a,16)
            if address in changes:raise ValueError('SRAM/FastROM recipes overlap')
            changes[address]=('$'+old,'$'+new)
    recipe='arch 65816\nlorom\n'
    for a,(old,new) in sorted(changes.items()):recipe+=f'; @expect ${a:06X} {old}\norg ${a:06X}\ndb {new}\n'
    return recipe


def apply_source(base, text):
    rom, written, expected = bytearray(base), set(), set()
    pc = None
    previous = -1
    declarations = []
    for number, raw in enumerate(text.splitlines(), 1):
        try:
            assertion = re.fullmatch(r"\s*; @expect \$([0-9a-fA-F]{6})\s+(.+)", raw)
            if assertion:
                start = cpu_to_pc(int(assertion[1], 16), len(base))
                payload = byte_list(assertion[2].strip())
                if start // 0x8000 != (start + len(payload) - 1) // 0x8000:
                    raise ValueError("Base assertion crosses a bank")
                if base[start:start + len(payload)] != payload:
                    raise ValueError("Original-byte assertion failed")
                expected.update(range(start, start + len(payload)))
                continue
            line = raw.split(";", 1)[0].strip()
            if not line:
                continue
            if line in {"arch 65816", "lorom"}:
                declarations.append(line)
                continue
            match = re.fullmatch(r"org \$([0-9a-fA-F]{6})", line)
            if match:
                pc = cpu_to_pc(int(match[1], 16), len(base))
                continue
            match = re.fullmatch(r"db\s+(.+)", line)
            if not match or pc is None:
                raise ValueError(f"Unsupported syntax or db before org: {line}")
            payload = byte_list(match[1].strip())
            end = pc + len(payload)
            if end > len(base) or pc // 0x8000 != (end - 1) // 0x8000:
                raise ValueError("Write crosses ROM end or LoROM bank")
            span = set(range(pc, end))
            if span & written or pc <= previous:
                raise ValueError("Overlapping or out-of-order physical write")
            if not span <= expected:
                raise ValueError("Write lacks verified @expect base bytes")
            rom[pc:end] = payload
            written.update(span)
            previous, pc = end - 1, end
        except ValueError as error:
            raise ValueError(f"ASM line {number}: {error}") from error
    if declarations != ["arch 65816", "lorom"]:
        raise ValueError("Source must declare arch 65816 followed by lorom once")
    if rom != base:
        # Checksum algorithm is valid for the currently fixed, power-of-two size.
        rom[0x7FDC:0x7FE0] = bytes((0xFF, 0xFF, 0, 0))
        checksum = sum(rom) & 0xFFFF
        rom[0x7FDC:0x7FE0] = ((checksum ^ 0xFFFF).to_bytes(2, "little")
                                 + checksum.to_bytes(2, "little"))
    return bytes(rom), len(written)


def feature_recipe(text, feature):
    """Resolve a complete, uniquely addressed inline feature recipe."""
    expects = re.findall(rf'^; @{feature}_expect \$([A-F0-9]{{6}}) (.+)$', text, re.M)
    writes = re.findall(rf'^; @{feature}_db \$([A-F0-9]{{6}}) (.+)$', text, re.M)
    expected, records = dict(expects), dict(writes)
    if (not records or len(expected) != len(expects) or len(records) != len(writes)
            or expected.keys() != records.keys()):
        raise ValueError(f'Missing, duplicate or mismatched {feature} recipes')
    return 'arch 65816\nlorom\n' + ''.join(
        f'; @expect ${a} {expected[a]}\norg ${a}\ndb {new}\n'
        for a, new in sorted(records.items()))


def build_release(expanded, text, variant):
    if variant not in ('spell_select', 'weapon_types', 'air_combat', 'script_opening'):
        return apply_source(expanded, sram_recipe(text, variant))
    # Punch/Hard/Status assert against the original expanded base. Selection
    # replaces Hard's startup hook, so its assertions target the Status image.
    recipe = sram_recipe(text, 'fast')
    for feature in ('punch', 'hard', 'status'):
        recipe += feature_recipe(text, feature).removeprefix('arch 65816\nlorom\n')
    records = re.findall(r'; @expect \$([A-F0-9]{6}) (.+)\norg \$[A-F0-9]{6}\ndb (.+)\n', recipe)
    recipe = 'arch 65816\nlorom\n' + ''.join(
        f'; @expect ${a} {old}\norg ${a}\ndb {new}\n'
        for a, old, new in sorted(records))
    prior, count = apply_source(expanded, recipe)
    output, selected_count = apply_source(prior, feature_recipe(text, 'select'))
    count += selected_count
    if variant in ('weapon_types', 'air_combat', 'script_opening'):
        # Each accepted pass asserts against its immediate predecessor, including
        # intentional replacement hooks. All bytes come from this single ASM.
        for feature in ('menu', 'srmonly', 'savelevel', 'weapon'):
            output, feature_count = apply_source(output, feature_recipe(text, feature))
            count += feature_count
    if variant in ('air_combat','script_opening'):
        for feature in ('encounter', 'heroname', 'mpoints', 'aircombat', 'universal', 'bettergear'):
            output, feature_count = apply_source(output, feature_recipe(text, feature))
            count += feature_count
    if variant=='script_opening':
        start=int(metadata(text,'script_reserve_start'));size=int(metadata(text,'script_reserve_size'))
        if len(output)!=0x400000 or (start,size)!=(0x3e0000,0x20000):
            raise ValueError('Script reservation must be the final128KiB of4MiB ROM')
        if output[start:]!=bytes([255])*size:
            raise ValueError('Earlier feature writes overlap reserved script banks')
        output,feature_count=apply_source(output,feature_recipe(text,'opening'))
        count+=feature_count
        if re.search(r'^; @service_db ', text, re.M):
            output, feature_count = apply_source(output, feature_recipe(text, 'service'))
            count += feature_count
        if re.search(r'^; @yokan_db ', text, re.M):
            output, feature_count = apply_source(output, feature_recipe(text, 'yokan'))
            count += feature_count
        if re.search(r'^; @horizon_db ', text, re.M):
            output, feature_count = apply_source(output, feature_recipe(text, 'horizon'))
            count += feature_count
        if re.search(r'^; @sharednames_db ', text, re.M):
            output, feature_count = apply_source(output, feature_recipe(text, 'sharednames'))
            count += feature_count
        if re.search(r'^; @field_db ', text, re.M):
            output, feature_count = apply_source(output, feature_recipe(text, 'field'))
            count += feature_count
        if re.search(r'^; @npc_db ', text, re.M):
            output, feature_count = apply_source(output, feature_recipe(text, 'npc'))
            count += feature_count
        if re.search(r'^; @battle_db ', text, re.M):
            output, feature_count = apply_source(output, feature_recipe(text, 'battle'))
            count += feature_count
        if re.search(r'^; @ending_db ', text, re.M):
            output, feature_count = apply_source(output, feature_recipe(text, 'ending'))
            count += feature_count
        if re.search(r'^; @story_db ', text, re.M):
            output, feature_count = apply_source(output, feature_recipe(text, 'story'))
            count += feature_count
    if re.search(r'^; @soundtrack_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'soundtrack'))
        count += feature_count
    if re.search(r'^; @arena_music_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'arena_music'))
        count += feature_count
    if re.search(r'^; @coopcash_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'coopcash'))
        count += feature_count
    if re.search(r'^; @walkxp_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'walkxp'))
        count += feature_count
    if re.search(r'^; @titlegfx_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'titlegfx'))
        count += feature_count
    if re.search(r'^; @nextxp_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'nextxp'))
        count += feature_count
    if re.search(r'^; @fastfollow_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'fastfollow'))
        count += feature_count
    if re.search(r'^; @fastall_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'fastall'))
        count += feature_count
    if re.search(r'^; @scriptpack_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'scriptpack'))
        count += feature_count
    if re.search(r'^; @qa015_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'qa015'))
        count += feature_count
    if re.search(r'^; @qa016_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'qa016'))
        count += feature_count
    if re.search(r'^; @qa017_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'qa017'))
        count += feature_count
    if re.search(r'^; @boobomb_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'boobomb'))
        count += feature_count
    if re.search(r'^; @meleetol_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'meleetol'))
        count += feature_count
    if re.search(r'^; @dragonhp_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'dragonhp'))
        count += feature_count
    if re.search(r'^; @quotatimer_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'quotatimer'))
        count += feature_count
    if re.search(r'^; @qa022_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'qa022'))
        count += feature_count
    if re.search(r'^; @mrfboss_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'mrfboss'))
        count += feature_count
    if re.search(r'^; @mrfvictory_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'mrfvictory'))
        count += feature_count
    if re.search(r'^; @mrfaccess_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'mrfaccess'))
        count += feature_count
    if re.search(r'^; @mrfstory_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'mrfstory'))
        count += feature_count
    if re.search(r'^; @mrfcustom_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'mrfcustom'))
        count += feature_count
    if re.search(r'^; @mrfframe_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'mrfframe'))
        count += feature_count
    if re.search(r'^; @weapondrop_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'weapondrop'))
        count += feature_count
    if re.search(r'^; @npcappend_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'npcappend'))
        count += feature_count
    if re.search(r'^; @weaponbarrier_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'weaponbarrier'))
        count += feature_count
    if re.search(r'^; @highjump_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'highjump'))
        count += feature_count
    if re.search(r'^; @acost_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'acost'))
        count += feature_count
    if re.search(r'^; @mcap_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'mcap'))
        count += feature_count
    if re.search(r'^; @sknp_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'sknp'))
        count += feature_count
    if re.search(r'^; @substitute_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'substitute'))
        count += feature_count
    if re.search(r'^; @secret_town_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'secret_town'))
        count += feature_count
    if re.search(r'^; @secretfix_db ', text, re.M):
        output, feature_count = apply_source(output, feature_recipe(text, 'secretfix'))
        count += feature_count
    return output, count


def inspect(base):
    print(f"Size: {len(base)} bytes; SHA-256: {hashlib.sha256(base).hexdigest()}")
    print(f"CRC32: {zlib.crc32(base):08X}")
    print(f"Title: {base[0x7FC0:0x7FD5].decode('ascii')!r}")
    print("Header PC $007FC0: " + base[0x7FC0:0x8000].hex(" ").upper())
    print(f"Measured checksum: ${sum(base) & 0xFFFF:04X}")
    for name, offset in (("native NMI", 0x7FEA), ("native IRQ", 0x7FEE),
                         ("reset", 0x7FFC)):
        address = int.from_bytes(base[offset:offset + 2], "little")
        pc = cpu_to_pc(address, len(base))
        print(f"{name}: CPU $00:{address:04X}, PC ${pc:06X}; "
              + base[pc:pc + 32].hex(" ").upper())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_rom", nargs="?", type=Path, default=DEFAULT_BASE)
    parser.add_argument("output_rom", nargs="?", type=Path)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--inspect", action="store_true", help="Read-only base report")
    args = parser.parse_args()
    try:
        text = args.source.read_text(encoding="utf-8")
        base = args.base_rom.read_bytes()
        size = int(metadata(text, "base_size"))
        if len(base) != size or hashlib.sha256(base).hexdigest() != metadata(text, "base_sha256"):
            raise ValueError("Base ROM size/SHA-256 does not match the ASM identity")
        output_size=int(metadata(text,"output_size"))
        if size != 0x100000 or output_size not in (size,0x200000,0x400000):
            raise ValueError("Unsupported mapping/checksum contract")
        if output_size in (0x200000,0x400000):
            if int(metadata(text,'sram_output_size'))!=output_size:raise ValueError('SRAM output size mismatch')
            variant=metadata(text,'release_variant')
        else:recipe=text
        if args.inspect:
            inspect(base)
            return 0
        if args.output_rom is None:args.output_rom=args.source.with_suffix('.sfc')
        if args.output_rom.resolve() in {args.base_rom.resolve(), args.source.resolve()}:
            raise ValueError("Output must not overwrite the base or ASM source")
        if not args.output_rom.name.startswith(("Janky_Ninja_Boy", "Super_Ninja_Boyz")):
            raise ValueError("Output ROM name must begin with Janky_Ninja_Boy or Super_Ninja_Boyz")
        expanded=base+bytes([255])*(output_size-size)
        output, count = (build_release(expanded, text, variant) if output_size in (0x200000,0x400000)
                         else apply_source(expanded, recipe))
        if output[0x7fd7]!={0x100000:10,0x200000:11,0x400000:12}[output_size]:
            raise ValueError('ROM size header does not match declared output size')
        args.output_rom.write_bytes(output)
        print(f"Built: {args.output_rom}")
        print(f"Explicit source bytes: {count}; size: {len(output)}; identical to base: {output == base}")
        print(f"SHA-256: {hashlib.sha256(output).hexdigest()}")
        return 0
    except (ValueError, OSError) as error:
        parser.exit(1, f"Build error: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
