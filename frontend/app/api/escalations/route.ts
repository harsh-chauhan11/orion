import { NextResponse } from "next/server";
import { execFile } from "child_process";
import { promisify } from "util";
import path from "path";

const execFileAsync = promisify(execFile);

export async function GET() {
  try {
    const backendPath = path.resolve(
      process.cwd(),
      "..",
      "backend"
    );

    const scriptPath = path.join(
      backendPath,
      "src",
      "escalation_api.py"
    );

    const { stdout } = await execFileAsync(
      "uv",
      ["run", "python", scriptPath],
      {
        cwd: backendPath,
        windowsHide: true,
      }
    );

    const escalations = JSON.parse(stdout);

    return NextResponse.json({
      success: true,
      escalations,
    });
  } catch (error) {
    console.error("Failed to load escalations:", error);

    return NextResponse.json(
      {
        success: false,
        error: "Failed to load escalation requests.",
      },
      { status: 500 }
    );
  }
}