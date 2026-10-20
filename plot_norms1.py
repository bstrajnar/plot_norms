import os
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def extract_spectral_norms(file_path):
    with open(file_path, "r", errors="ignore") as f:
        content = f.read()

    # Ujemi PREDICTOR ali CORRECTOR blok
    block_re = re.compile(
        r"NORMS AT NSTEP CNT4 \((?P<phase>PREDICTOR|CORRECTOR)\)\s+(?P<tstep>\d+).*?"
        r"SPECTRAL NORMS -\s+LOG\(PREHYDS\)\s+(?P<log_prehyds>[\d.E+-]+).*?"
        r"LEV\s+VORTICITY\s+DIVERGENCE\s+TEMPERATURE(?:\s+HUMIDITY)?\s+KINETIC ENERGY\s+"
        r"AVE\s+(?P<ave_line>[^\r\n]+).*?"
        r"LEV\s+LOG\(PRE/PREHYD\).*?"
        r"AVE\s+(?P<ave_log_line>[^\r\n]+)",
        re.DOTALL,
    )

    float_re = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[Ee][+-]?\d+)?")

    rows = []
    for m in block_re.finditer(content):
        tstep = int(m.group("tstep"))
        log_prehyds = float(m.group("log_prehyds"))

        # Prva AVE vrstica
        ave_line = m.group("ave_line").split("#", 1)[0]
        ave_vals = [float(x) for x in float_re.findall(ave_line)]
        if len(ave_vals) == 5:
            vorticity, divergence, temperature, humidity, kinetic = ave_vals
        elif len(ave_vals) == 4:
            vorticity, divergence, temperature, kinetic = ave_vals
            humidity = None
        else:
            continue

        # Zadnja AVE vrstica (LOG_PRE_PREHYD, VERTICAL_DIVERGENCE)
        ave_log_line = m.group("ave_log_line").split("#", 1)[0]
        ave_log_vals = [float(x) for x in float_re.findall(ave_log_line)]
        if len(ave_log_vals) >= 2:
            log_pre_prehyd = ave_log_vals[0]
            ver_div = ave_log_vals[1]
        else:
            log_pre_prehyd = float('nan')
            ver_div = float('nan')

        rows.append(
            (
                tstep,
                log_prehyds,
                vorticity,
                divergence,
                temperature,
                humidity,
                kinetic,
                log_pre_prehyd,
                ver_div,
                m.group("phase")  # Dodamo še, da vemo ali je Predictor ali Corrector
            )
        )

    df = pd.DataFrame(
        rows,
        columns=[
            "TSTEP",
            "LOG_PREHYDS",
            "VORTICITY",
            "DIVERGENCE",
            "TEMPERATURE",
            "HUMIDITY",
            "KINETIC_ENERGY",
            "LOG_PRE_PREHYD",
            "VERTICAL_DIVERGENCE",
            "PHASE",  # Predictor ali Corrector
        ],
    )
    return df
def extract_timestep_from_filename(filename):
    """Izlušči timestep v sekundah iz imena NODE fajla (npr. NODE_alaro_30s)."""
    match = re.search(r"_(\d+)s", filename)
    if match:
        return int(match.group(1))
    else:
        raise ValueError(f"❌ Timestep not found in filename: {filename}")


def plot_field_across_nodes(
    node_files, field="LOG_PREHYDS", output_filename="combined_plot.png", phase="CORRECTOR"
):
    """
    Plots a specified field across multiple node files.
    
    Args:
        node_files (list): List of file paths to node output files.
        field (str): Column name to plot (e.g., 'LOG_PREHYDS', 'VERTICAL_DIVERGENCE').
        output_filename (str): Name of the output PNG file.
        phase (str): 'PREDICTOR' or 'CORRECTOR' to select which steps to plot.
    """
    plt.figure(figsize=(12, 6))

    for node_file in node_files:
        print(f"🔍 Processing: {node_file}")
        timestep_seconds = 45  # ali extract_timestep_from_filename(node_file)
        df = extract_spectral_norms(node_file)

        # Filtriraj po phase (Predictor ali Corrector)
        df = df[df["PHASE"] == phase]

        if df.empty:
            print(f"⚠️ No {phase} data found in file: {node_file}")
            continue

        df["time_hours"] = df["TSTEP"] * timestep_seconds / 3600.0

        if field not in df.columns:
            print(f"⚠️ Field '{field}' not found in file: {node_file}")
            continue

        # tmp: cut at 1 hour
        df = df[:80]

        label = f"{os.path.basename(node_file)}"
        plt.plot(df["time_hours"], df[field], label=label)

        # X-os označena samo pri polnih urah
        max_hours = int(df["time_hours"].max()) + 1
        plt.xticks(np.arange(0, max_hours + 1, 1))

    plt.title(f"Spectral norm: {field}")
    plt.xlabel("Time [hours]")
    plt.ylabel("Value")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(output_filename, dpi=300)
    print(f"✅ Combined plot saved as: {output_filename}")

# Primer uporabe:
# nodes_alaro_refdyn = [
#    "extracted_nodes/NODE_alaro_20s",
#    "extracted_nodes/NODE_alaro_30s",
##   "extracted_nodes/NODE_alaro_newdyn_30s",
##   "extracted_nodes/NODE_alaro_newdyn_20s",
##   "extracted_nodes/NODE_alaro_newdyn_oro_30s"
# ]
nodes_alaro_newdyn = [
    "extracted_nodes/NODE_alaro_20s",
    "extracted_nodes/NODE_alaro_30s",
    "extracted_nodes/NODE_alaro_newdyn_20s",
    "extracted_nodes/NODE_alaro_newdyn_30s",
    "extracted_nodes/NODE_alaro_newdyn_oro_30s"
]
# nodes_arome_refdyn = [
#    "extracted_nodes/NODE_arome_20s",
#    "extracted_nodes/NODE_arome_30s",
##   "extracted_nodes/NODE_arome_newdyn_30s",
##   "extracted_nodes/NODE_arome_newdyn_20s",
##   "extracted_nodes/NODE_arome_newdyn_30s_SP",
##   "extracted_nodes/NODE_arome_newdyn_oro_30s"
# ]
#
nodes_arome_newdyn = [
   "extracted_nodes/NODE_arome_20s",
   "extracted_nodes/NODE_arome_30s",
   "extracted_nodes/NODE_arome_newdyn_20s",
   "extracted_nodes/NODE_arome_newdyn_30s",
   "extracted_nodes/NODE_arome_newdyn_30s_SP",
   "extracted_nodes/NODE_arome_newdyn_oro_30s"
 ]
claef1k_60 = [
    "claef1k_60/NODE.001_1_01_fg",
    "claef1k_60/NODE.001_1_01_3dvar_M0_MASTERODB",
#    "claef1k_60/NODE.001_1_01_3dvar_OOPS",
#    "claef1k_60/NODE_3denvar32_spectralinput_iau0.5h",
#    "claef1k_60/NODE_3denvar32_spectralinput_iau1h",
#    "claef1k_60/NODE_3denvar32_spectralinput_iau0.25h",
#    "claef1k_60/NODE_3denvar20_spectralinput_iau0.25h",
#    "claef1k_60/NODE_3denvar32_spectralinput_iau5min",
#    "claef1k_60/NODE_3denvar32_iau5min",
    "claef1k_60/NODE_3denvar32_iau5min",
    "claef1k_60/NODE_3denvar32_iau15min",
    ]

claef1k_45 = [
    "claef1k_45/3denvar_32m",
#    "claef1k_45/NODE_3denvar34",
#    "claef1k_45/NODE_3dvar_M1_OOPS",
    "claef1k_45/fg",
#    "claef1k_45/NODE_3denvar34_OLD3",
    "claef1k_45/3denvar_32m_iau_5min",
    "claef1k_45/3denvar_32m_iau_15min",
#    "claef1k_45/NODE_3denvar30_iau15min",
#    "claef1k_45/NODE_3denvar20_iau15min",
#    "claef1k_45/NODE_3denvar10_iau15min",
     "claef1k_45/3dvar_M1",
#    "claef1k_45/NODE_3dvar_M0_MASTERODB",

]

claef1k_memb = [
    "claef1k_45/NODE_3denvar32",
    "claef1k_45/NODE_fromfg",
    "claef1k_45/NODE_3denvar32_iau15min",
    "claef1k_45/NODE_3denvar30_iau15min",
    "claef1k_45/NODE_3denvar10_iau15min",
    "claef1k_45/NODE_3denvar20_iau15min",
]




adiab_exps = [
        "adiab_nodes/NODE_arome_adiab_orig",
        "adiab_nodes/NODE_arome_adiab_nd4sys",
        "adiab_nodes/NODE_alaro_adiab_orig",
        "adiab_nodes/NODE_alaro_adiab_nd4sys",
]

adiab_exps1 = [
        "adiab_nodes/NODE_arome_adiab_1",
        "adiab_nodes/NODE_arome_adiab_1_nd4sys",
        "adiab_nodes/NODE_alaro_adiab_orig",
        "adiab_nodes/NODE_alaro_adiab_nd4sys",
]

adiab_exps2 = [
        "adiab_nodes/NODE_arome_adiab_2",
        "adiab_nodes/NODE_arome_adiab_2_nd4sys",
        "adiab_nodes/NODE_alaro_adiab_orig",
        "adiab_nodes/NODE_alaro_adiab_nd4sys",
]

adiab_exps3 = [
        "adiab_nodes/NODE_arome_adiab_3",
        "adiab_nodes/NODE_arome_adiab_3_nd4sys",
        "adiab_nodes/NODE_alaro_adiab_orig",
        "adiab_nodes/NODE_alaro_adiab_nd4sys",
]

adiab_modif1 = [
        "adiab_nodes/NODE_alaro_adiab_orig",
        "adiab_nodes/NODE_alaro_adiab_newdyn",
        "adiab_nodes/NODE_arome_adiab_orig",
        "adiab_nodes/NODE_arome_adiab_newdyn",
        "adiab_nodes/NODE_arome_adiab_1",
        "adiab_nodes/NODE_arome_adiab_1_newdyn",
]

adiab_alaro = [ 
        "adiab_nodes/NODE_alaro_adiab_orig",
        "adiab_nodes/NODE_alaro_adiab_orig_vesl005",
        "adiab_nodes/NODE_alaro_adiab_newdyn",
        "adiab_nodes/NODE_alaro_adiab_newdyn_vesl005",
#        "adiab_nodes/NODE_arome_adiab_orig",
#        "adiab_nodes/NODE_arome_adiab_newdyn",
]

alaro_arome = [
    "extracted_nodes/NODE_arome_20s",
    "extracted_nodes/NODE_arome_newdyn_20s",
    "extracted_nodes/NODE_alaro_20s",
    "extracted_nodes/NODE_alaro_newdyn_20s",
]

fields = [
    "LOG_PREHYDS",
    "VORTICITY",
    "DIVERGENCE",
    "TEMPERATURE",
    "KINETIC_ENERGY",
    "LOG_PRE_PREHYD",
    "VERTICAL_DIVERGENCE",
]

cy48t3_alaro_vesl = [
    "vesl_cy48t3/NODE_alaro_newdin",
    "vesl_cy48t3/NODE_alaro_newdin_vesl005",
    "vesl_cy48t3/NODE_alaro_orig",
    "vesl_cy48t3/NODE_alaro_orig_vesl005",
]

cy48t3_arome_200 = [
    "Lju200_nodes/node_arome_new_dyn",
    "Lju200_nodes/node_arome_old_dyn",
    "Lju200_nodes/node_alaro_olddyn",
    "Lju200_nodes/node_alaro_newdyn",
]
cy48t3_arome_500 = [
    "node_arom48t3_olddyn",
]
# fields = ["VORTICITY", "DIVERGENCE", "KINETIC_ENERGY"]for field in fields:
    #plot_field_across_nodes(
for field in fields:
    plot_field_across_nodes(claef1k_45, field=field, output_filename=f"claef1k_45_case2025092412_{field}.png")
    #plot_field_across_nodes(claef1k_60, field=field, output_filename=f"claef1k_60_case2025092412_{field}.png")
    #plot_field_across_nodes(claef1k_memb, field=field, output_filename=f"claef1k_memb_case2025092412_{field}.png")
    #plot_field_across_nodes(adiab_modif1, field=field, output_filename=f"combined_adiab_modif1_vesl_{field}.png")
    #plot_field_across_nodes(adiab_exps, field=field, output_filename=f"combined_adiab_exps_newdyn_{field}.png")
    #plot_field_across_nodes(adiab_exps1, field=field, output_filename=f"combined_adiab_exps1_newdyn_{field}.png")
    #plot_field_across_nodes(adiab_exps2, field=field, output_filename=f"combined_adiab_exps2_newdyn_{field}.png")
    #plot_field_across_nodes(adiab_exps3, field=field, output_filename=f"combined_adiab_exps3_newdyn_{field}.png")
#        nodes_claef, field=field, output_filename=f"combined_claef_adiab_{field}.png"
#    )
    # plot_field_across_nodes(nodes_alaro_refdyn, field=field, output_filename=f"combined_alaro_refdyn_{field}.png")
    # plot_field_across_nodes(nodes_alaro_newdyn, field=field, output_filename=f"combined_alaro_newdyn_{field}.png")
    #plot_field_across_nodes(nodes_arome_refdyn, field=field, output_filename=f"combined_arome_refdyn_{field}.png")
    # plot_field_across_nodes(nodes_arome_newdyn, field=field, output_filename=f"combined_arome_newdyn_{field}.png")
