import { CustomEditor, type ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { matchesKey } from "@earendil-works/pi-tui";

const DOUBLE_ESCAPE_WINDOW_MS = 500;

class DoubleEscapeClearEditor extends CustomEditor {
	private lastEscapeAt = 0;

	handleInput(data: string): void {
		if (matchesKey(data, "escape")) {
			const now = Date.now();
			const hasText = this.getText().length > 0;

			if (hasText && now - this.lastEscapeAt < DOUBLE_ESCAPE_WINDOW_MS) {
				this.setText("");
				this.lastEscapeAt = 0;
				return;
			}

			this.lastEscapeAt = hasText ? now : 0;
			super.handleInput(data);
			return;
		}

		this.lastEscapeAt = 0;
		super.handleInput(data);
	}
}

export default function (pi: ExtensionAPI) {
	pi.on("session_start", (_event, ctx) => {
		if (ctx.mode !== "tui" || ctx.ui.getEditorComponent()) return;
		ctx.ui.setEditorComponent((tui, theme, keybindings) =>
			new DoubleEscapeClearEditor(tui, theme, keybindings),
		);
	});
}
