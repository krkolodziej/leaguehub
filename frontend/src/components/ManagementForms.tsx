import { zodResolver } from '@hookform/resolvers/zod'
import { useForm, type FieldValues, type SubmitHandler, type UseFormRegisterReturn, type UseFormReturn } from 'react-hook-form'
import type { ReactNode } from 'react'
import { z } from 'zod'

import { errorMessage } from '../lib/errors'
import {
  useAddRosterEntry,
  useAddSeasonTeam,
  useCreateLeague,
  useCreateOrganization,
  useCreatePlayer,
  useCreateSeason,
  useCreateTeam,
} from '../lib/management'

const organizationSchema = z.object({ name: z.string().trim().min(2, 'Name must have at least 2 characters.'), slug: z.string().trim().min(2, 'Slug must have at least 2 characters.').regex(/^[a-z0-9-]+$/, 'Use lowercase letters, numbers and hyphens.') })
const leagueSchema = organizationSchema.extend({ description: z.string().max(500) })
const seasonSchema = z.object({ name: z.string().trim().min(1, 'Name is required.'), start_date: z.string().min(1, 'Start date is required.'), end_date: z.string().optional() })
const playerSchema = z.object({ first_name: z.string().trim().min(1, 'First name is required.'), last_name: z.string().trim().min(1, 'Last name is required.'), date_of_birth: z.string().optional() })
const rosterSchema = z.object({ player_id: z.number().positive(), shirt_number: z.number().int().positive().optional(), position: z.string().max(50).optional(), is_captain: z.boolean() })

type FormProps = { organizationId: number; onSuccess?: () => void }

function FieldError({ message }: { message?: string }) {
  return message ? <span className="field-error">{message}</span> : null
}

function FormError({ error }: { error: unknown }) {
  return error ? <div className="form-error" role="alert">{errorMessage(error)}</div> : null
}

export function OrganizationForm({ onSuccess }: { onSuccess?: () => void }) {
  const mutation = useCreateOrganization()
  const form = useForm<z.infer<typeof organizationSchema>>({ resolver: zodResolver(organizationSchema), defaultValues: { name: '', slug: '' } })
  const submit = (values: z.infer<typeof organizationSchema>) => mutation.mutate(values, { onSuccess: () => { form.reset(); onSuccess?.() } })
  return <FormCard title="Create organization" form={form} onSubmit={submit} pending={mutation.isPending} error={mutation.error} submitLabel="Create organization"><TextInput label="Name" registration={form.register('name')} error={form.formState.errors.name?.message} /><TextInput label="Slug" hint="lowercase-with-hyphens" registration={form.register('slug')} error={form.formState.errors.slug?.message} /></FormCard>
}

export function LeagueForm({ organizationId, onSuccess }: FormProps) {
  const mutation = useCreateLeague(organizationId)
  const form = useForm<z.infer<typeof leagueSchema>>({ resolver: zodResolver(leagueSchema), defaultValues: { name: '', slug: '', description: '' } })
  const submit = (values: z.infer<typeof leagueSchema>) => mutation.mutate(values, { onSuccess: () => { form.reset(); onSuccess?.() } })
  return <FormCard title="Add league" form={form} onSubmit={submit} pending={mutation.isPending} error={mutation.error} submitLabel="Add league"><TextInput label="Name" registration={form.register('name')} error={form.formState.errors.name?.message} /><TextInput label="Slug" registration={form.register('slug')} error={form.formState.errors.slug?.message} /><TextInput label="Description" registration={form.register('description')} error={form.formState.errors.description?.message} /></FormCard>
}

export function SeasonForm({ organizationId, leagueId, onSuccess }: FormProps & { leagueId: number }) {
  const mutation = useCreateSeason(organizationId, leagueId)
  const form = useForm<z.infer<typeof seasonSchema>>({ resolver: zodResolver(seasonSchema), defaultValues: { name: '', start_date: '', end_date: '' } })
  const submit = (values: z.infer<typeof seasonSchema>) => mutation.mutate({ ...values, end_date: values.end_date || undefined }, { onSuccess: () => { form.reset(); onSuccess?.() } })
  return <FormCard title="Add season" form={form} onSubmit={submit} pending={mutation.isPending} error={mutation.error} submitLabel="Add season"><TextInput label="Name" registration={form.register('name')} error={form.formState.errors.name?.message} /><TextInput label="Start date" type="date" registration={form.register('start_date')} error={form.formState.errors.start_date?.message} /><TextInput label="End date" type="date" registration={form.register('end_date')} error={form.formState.errors.end_date?.message} /></FormCard>
}

export function TeamForm({ organizationId, onSuccess }: FormProps) {
  const mutation = useCreateTeam(organizationId)
  const form = useForm<z.infer<typeof organizationSchema>>({ resolver: zodResolver(organizationSchema), defaultValues: { name: '', slug: '' } })
  const submit = (values: z.infer<typeof organizationSchema>) => mutation.mutate(values, { onSuccess: () => { form.reset(); onSuccess?.() } })
  return <FormCard title="Add team" form={form} onSubmit={submit} pending={mutation.isPending} error={mutation.error} submitLabel="Add team"><TextInput label="Name" registration={form.register('name')} error={form.formState.errors.name?.message} /><TextInput label="Slug" registration={form.register('slug')} error={form.formState.errors.slug?.message} /></FormCard>
}

export function PlayerForm({ organizationId, onSuccess }: FormProps) {
  const mutation = useCreatePlayer(organizationId)
  const form = useForm<z.infer<typeof playerSchema>>({ resolver: zodResolver(playerSchema), defaultValues: { first_name: '', last_name: '', date_of_birth: '' } })
  const submit = (values: z.infer<typeof playerSchema>) => mutation.mutate({ ...values, date_of_birth: values.date_of_birth || undefined }, { onSuccess: () => { form.reset(); onSuccess?.() } })
  return <FormCard title="Add player" form={form} onSubmit={submit} pending={mutation.isPending} error={mutation.error} submitLabel="Add player"><TextInput label="First name" registration={form.register('first_name')} error={form.formState.errors.first_name?.message} /><TextInput label="Last name" registration={form.register('last_name')} error={form.formState.errors.last_name?.message} /><TextInput label="Date of birth" type="date" registration={form.register('date_of_birth')} error={form.formState.errors.date_of_birth?.message} /></FormCard>
}

export function SeasonTeamForm({ organizationId, leagueId, seasonId, teams, onSuccess }: FormProps & { leagueId: number; seasonId: number; teams: { id: number; name: string }[] }) {
  const mutation = useAddSeasonTeam(organizationId, leagueId, seasonId)
  const form = useForm<{ team_id: number }>({ resolver: zodResolver(z.object({ team_id: z.number().positive('Choose a team.') })), defaultValues: { team_id: 0 } })
  const submit = (values: { team_id: number }) => mutation.mutate(values.team_id, { onSuccess: () => { form.reset(); onSuccess?.() } })
  return <FormCard title="Add team to season" form={form} onSubmit={submit} pending={mutation.isPending} error={mutation.error} submitLabel="Add to season"><label>Team<select {...form.register('team_id', { valueAsNumber: true })}><option value={0}>Choose a team…</option>{teams.map((team) => <option key={team.id} value={team.id}>{team.name}</option>)}</select><FieldError message={form.formState.errors.team_id?.message} /></label></FormCard>
}

export function RosterForm({ organizationId, leagueId, seasonId, seasonTeamId, players, onSuccess }: FormProps & { leagueId: number; seasonId: number; seasonTeamId: number; players: { id: number; full_name: string }[] }) {
  const mutation = useAddRosterEntry(organizationId, leagueId, seasonId, seasonTeamId)
  const form = useForm<z.infer<typeof rosterSchema>>({ resolver: zodResolver(rosterSchema), defaultValues: { player_id: 0, shirt_number: undefined, position: '', is_captain: false } })
  const submit = (values: z.infer<typeof rosterSchema>) => mutation.mutate(values, { onSuccess: () => { form.reset(); onSuccess?.() } })
  return <FormCard title="Add roster player" form={form} onSubmit={submit} pending={mutation.isPending} error={mutation.error} submitLabel="Add player"><label>Player<select {...form.register('player_id', { valueAsNumber: true })}><option value={0}>Choose a player…</option>{players.map((player) => <option key={player.id} value={player.id}>{player.full_name}</option>)}</select><FieldError message={form.formState.errors.player_id?.message} /></label><TextInput label="Shirt number" type="number" registration={form.register('shirt_number', { setValueAs: (value) => value === '' ? undefined : Number(value) })} error={form.formState.errors.shirt_number?.message} /><TextInput label="Position" registration={form.register('position')} error={form.formState.errors.position?.message} /><label className="checkbox-label"><input type="checkbox" {...form.register('is_captain')} /> Captain</label></FormCard>
}

function TextInput({ label, type = 'text', hint, registration, error }: { label: string; type?: string; hint?: string; registration: UseFormRegisterReturn; error?: string }) {
  return <label>{label}{hint && <span className="field-hint">{hint}</span>}<input type={type} {...registration} /><FieldError message={error} /></label>
}

function FormCard<T extends FieldValues>({ title, form, onSubmit, pending, error, submitLabel, children }: { title: string; form: UseFormReturn<T>; onSubmit: SubmitHandler<T>; pending: boolean; error: unknown; submitLabel: string; children: ReactNode }) {
  return <section className="form-card"><h3>{title}</h3><FormError error={error} /><form className="form-stack compact" onSubmit={form.handleSubmit(onSubmit)}>{children}<button className="button button-primary" type="submit" disabled={pending}>{pending ? 'Saving…' : submitLabel}</button></form></section>
}
