# (Solo para el administrador) Invitar alumnos

Invitar a un alumno por su usuario de GitHub:

```bash
gh api -X PUT repos/Jumilo098/organigrama-quant/collaborators/USUARIO_GITHUB
```

Ver invitaciones pendientes y colaboradores:

```bash
gh api repos/Jumilo098/organigrama-quant/invitations --jq '.[].invitee.login'
gh api repos/Jumilo098/organigrama-quant/collaborators --jq '.[].login'
```

Quitar a alguien:

```bash
gh api -X DELETE repos/Jumilo098/organigrama-quant/collaborators/USUARIO_GITHUB
```

⚠️ En una cuenta personal con plan gratuito los colaboradores reciben permiso de **escritura** y `main` no se
puede proteger en un repo privado. Opciones: GitHub Pro (protección de rama), o mover el repo a una
organización gratuita donde a los alumnos se les da rol **Read** (solo lectura + fork + Pull Request) y se
gestionan por equipos.
