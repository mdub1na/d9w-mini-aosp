# Recovery operation status

Use one versioned status snapshot for the host and a future recovery display.
The current tool projects an existing R1 host receipt and its writer log. It
reads local files and uses the Python standard library.

```sh
python3 -B tools/recovery/progress.py /path/to/r1-operation-output
```

Pass the directory containing `uart-receipt.json` and, when available,
`progress.log`. A live observer can feed one writer line at a time to
`OperationProgress.observe()` and call `snapshot(receipt, link=…)` with the
latest receipt. Create a fresh observer for each operation, even when the
operation name repeats.

## Snapshot version 1

```json
{
  "version": 1,
  "operation": "install",
  "state": "running",
  "phase": "verify_partition",
  "partition": "data",
  "progress": {"completed": 2048, "total": 4096, "unit": "MiB"},
  "link": "connected"
}
```

| Field | Values |
| --- | --- |
| `operation` | `install`, `restore`, `collect`, or `reboot` |
| `state` | `waiting`, `ready`, `blocked`, `not_started`, `awaiting_start`, `running`, `unknown`, `verified`, `failed`, or `reboot_requested` |
| `phase` | For an observed start, `preflight`, `verify_source`, `write_partition`, `verify_partition`, `collect`, or `reboot`. Otherwise `null`. |
| `partition` | `system` or `data` for a partition phase. Otherwise `null`. |
| `progress` | Nonnegative integer `completed`, positive integer or `null` `total`, and `unit` of `items` or `MiB`. The whole object is `null` until a counter is available. |
| `link` | `connected` or `disconnected` from the active observer. The offline reader reports `unobserved`. |

The source count covers items checked by the writer. Installations include
implicit zero ranges and restores count files. Partition counters use the
writer's rounded-down MiB values. Each counter represents its own phase and
partition. A missing total is shown as indeterminate. Forward progress can
replace earlier observations. Repeated lines, regressing counters and
inconsistent totals leave the last observation intact.

## State and verification

- A matching `PLAN` receipt determines readiness. It authorizes no action by
  itself. An attempted `RUN` can be shown as `awaiting_start` only with an
  actively observed link and no receipt error.
- A matching `START` and an active receipt allow `running`. If contact is lost
  after `RUN`, retain the last phase and show `unknown` until authoritative
  evidence arrives. A host UI should show its observation age independently.
- The host records a validated `RESULT` with its operation and exit code.
  A successful, verified result establishes `verified`. A failed result
  establishes `failed`. Writer text and reaching the reported total remain
  progress observations. Render the terminal result as the headline and keep
  the last sampled counter as history. Show an active progress bar only while
  the operation is running.
- A successful reboot acknowledgement establishes `reboot_requested`.
  Confirming a new Android session requires separate boot evidence.
- The snapshot contains no command, private device identifier, UART nonce or
  raw writer output. A viewer can render a status panel from these fields while
  the device workflow separately determines write interlocks and safe exit.

The reader accepts the current R1 install, restore, collect and reboot receipts.
The installed UART protocol and TWRP UI require no change to use it on the
host. The [display-only TWRP panel](recovery-operation-panel.md) maps these
snapshots to a landscape page. A recovery-side producer may emit the same
shape using local writer observations when that integration is implemented.
