"""CLI entry point with git passthrough for unrecognized commands."""

from __future__ import annotations

import click

from gitdot import git


class DotGroup(click.Group):
    """Custom Click group that passes unrecognized commands through to git."""

    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        # Try built-in commands first
        cmd = super().get_command(ctx, cmd_name)
        if cmd is not None:
            return cmd
        # Pass through to git
        return self._make_passthrough(cmd_name)

    def resolve_command(
        self, ctx: click.Context, args: list[str]
    ) -> tuple[str | None, click.Command | None, list[str]]:
        # Prevent Click from erroring on unknown commands
        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            # If the command is not found, let get_command handle it
            cmd_name = args[0] if args else None
            cmd = self.get_command(ctx, cmd_name) if cmd_name else None
            return cmd_name, cmd, args[1:]

    def _make_passthrough(self, cmd_name: str) -> click.Command:
        @click.command(
            cmd_name,
            context_settings={
                "ignore_unknown_options": True,
                "allow_extra_args": True,
            },
        )
        @click.argument("args", nargs=-1, type=click.UNPROCESSED)
        @click.pass_context
        def passthrough(ctx: click.Context, args: tuple[str, ...]) -> None:
            result = git.run([cmd_name] + list(args), capture=False)
            ctx.exit(result.returncode)

        return passthrough


@click.group(cls=DotGroup)
@click.version_option(package_name="gitdot")
def main() -> None:
    """dot -- a beginner-friendly git interface."""


def _register_commands() -> None:
    from gitdot.save import save
    from gitdot.undo import undo
    from gitdot.switch import switch
    from gitdot.ignore import ignore
    from gitdot.amend import amend
    from gitdot.discard import discard
    from gitdot.push import push
    from gitdot.pull import pull

    main.add_command(save)
    main.add_command(undo)
    main.add_command(switch)
    main.add_command(ignore)
    main.add_command(amend)
    main.add_command(discard)
    main.add_command(push)
    main.add_command(pull)


_register_commands()
