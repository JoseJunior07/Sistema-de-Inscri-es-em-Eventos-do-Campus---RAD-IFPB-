from functools import wraps
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, View
from .models import Sala, Evento, Atividade, InscricaoEvento, InscricaoAtividade
from django.contrib.auth import login

# --- AUTENTICAÇÃO ---
class CadastroView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/cadastro.html"
    success_url = reverse_lazy("lista_eventos")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  # Loga o utilizador automaticamente
        return response


def eh_organizador(user):
    return user.groups.filter(name="Organizadores").exists()


def dono_do_evento_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        evento = get_object_or_404(Evento, pk=kwargs["pk"])
        if evento.organizador_id != request.user.pk:
            return HttpResponseForbidden("Você não é o organizador deste evento.")
        request.evento = evento
        return view_func(request, *args, **kwargs)
    return wrapper


# --- FORMULÁRIOS ---
class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ["nome", "descricao", "data_inicio", "data_fim", "inscricoes_abertas"]
        widgets = {
            "data_inicio": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "data_fim": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ["titulo", "tipo", "descricao", "responsavel", "sala", "inicio", "fim"]
        widgets = {
            "inicio": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "fim": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }


# --- VISTAS PÚBLICAS ---
def lista_eventos(request):
    eventos = Evento.objects.all()
    return render(request, "inscricoes/lista_eventos.html", {"eventos": eventos})


def detalhe_evento(request, pk):
    evento = get_object_or_404(Evento, pk=pk)
    atividades = evento.atividades.select_related("sala")
    inscrito = False
    inscricao_evento = None

    if request.user.is_authenticated:
        inscricao_evento = InscricaoEvento.objects.filter(
            evento=evento, participante=request.user
        ).first()
        inscrito = inscricao_evento is not None

    atividades_inscritas_ids = set()
    if inscrito:
        atividades_inscritas_ids = set(
            InscricaoAtividade.objects.filter(
                inscricao_evento=inscricao_evento
            ).values_list("atividade_id", flat=True)
        )

    return render(
        request,
        "inscricoes/detalhe_evento.html",
        {
            "evento": evento,
            "atividades": atividades,
            "inscrito": inscrito,
            "inscricao_evento": inscricao_evento,
            "atividades_inscritas_ids": atividades_inscritas_ids,
        },
    )


# --- ORGANIZADOR ---
@login_required
def criar_evento(request):
    if not eh_organizador(request.user):
        return HttpResponseForbidden("Apenas organizadores podem criar eventos.")
    if request.method == "POST":
        form = EventoForm(request.POST)
        if form.is_valid():
            evento = form.save(commit=False)
            evento.organizador = request.user
            evento.save()
            return redirect("detalhe_evento", pk=evento.pk)
    else:
        form = EventoForm()
    return render(request, "inscricoes/form_evento.html", {"form": form})


@dono_do_evento_required
def editar_evento(request, pk):
    evento = request.evento
    if request.method == "POST":
        form = EventoForm(request.POST, instance=evento)
        if form.is_valid():
            form.save()
            return redirect("detalhe_evento", pk=evento.pk)
    else:
        form = EventoForm(instance=evento)
    return render(request, "inscricoes/form_evento.html", {"form": form})


@dono_do_evento_required
def criar_atividade(request, pk):
    evento = request.evento
    if request.method == "POST":
        form = AtividadeForm(request.POST)
        if form.is_valid():
            atividade = form.save(commit=False)
            atividade.evento = evento

            if atividade.inicio < evento.data_inicio or atividade.fim > evento.data_fim:
                messages.error(request, "A atividade precisa acontecer dentro do período do evento.")
                return render(request, "inscricoes/form_atividade.html", {"form": form})

            if atividade.fim <= atividade.inicio:
                messages.error(request, "O fim da atividade não pode ser antes ou igual ao início.")
                return render(request, "inscricoes/form_atividade.html", {"form": form})

            # RN3: Sala ocupada em horário sobreposto
            conflito = Atividade.objects.filter(sala=atividade.sala).filter(
                inicio__lt=atividade.fim, fim__gt=atividade.inicio
            )
            if conflito.exists():
                messages.error(request, "Esta sala já está ocupada neste horário.")
                return render(request, "inscricoes/form_atividade.html", {"form": form})

            atividade.save()
            return redirect("detalhe_evento", pk=evento.pk)
    else:
        form = AtividadeForm()
    return render(request, "inscricoes/form_atividade.html", {"form": form})


@dono_do_evento_required
def editar_atividade(request, pk, atividade_pk):
    evento = request.evento
    atividade = get_object_or_404(Atividade, pk=atividade_pk, evento=evento)

    if request.method == "POST":
        form = AtividadeForm(request.POST, instance=atividade)
        if form.is_valid():
            nova_atividade = form.save(commit=False)

            if nova_atividade.inicio < evento.data_inicio or nova_atividade.fim > evento.data_fim:
                messages.error(request, "A atividade precisa acontecer dentro do período do evento.")
                return render(request, "inscricoes/form_atividade.html", {"form": form})

            if nova_atividade.fim <= nova_atividade.inicio:
                messages.error(request, "O fim da atividade não pode ser antes ou igual ao início.")
                return render(request, "inscricoes/form_atividade.html", {"form": form})

            # RN3: Ignora a própria atividade na validação de edição
            conflito = Atividade.objects.filter(sala=nova_atividade.sala).exclude(pk=atividade.pk).filter(
                inicio__lt=nova_atividade.fim, fim__gt=nova_atividade.inicio
            )
            if conflito.exists():
                messages.error(request, "Esta sala já está ocupada neste horário.")
                return render(request, "inscricoes/form_atividade.html", {"form": form})

            nova_atividade.save()
            return redirect("detalhe_evento", pk=evento.pk)
    else:
        form = AtividadeForm(instance=atividade)
    return render(request, "inscricoes/form_atividade.html", {"form": form})


# --- INSCRIÇÕES ---
@login_required
def inscrever_evento(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    evento = get_object_or_404(Evento, pk=pk)

    if not evento.inscricoes_abertas:
        messages.error(request, "Este evento não está mais aceitando inscrições.")
        return redirect("detalhe_evento", pk=pk)

    if InscricaoEvento.objects.filter(evento=evento, participante=request.user).exists():
        messages.error(request, "Você já está inscrito neste evento.")
        return redirect("detalhe_evento", pk=pk)

    InscricaoEvento.objects.create(evento=evento, participante=request.user)
    return redirect("detalhe_evento", pk=pk)


@login_required
def inscrever_atividade(request, pk):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    atividade = get_object_or_404(Atividade, pk=pk)

    # RN4: Exige inscrição prévia no evento
    inscricao_evento = InscricaoEvento.objects.filter(
        evento=atividade.evento, participante=request.user
    ).first()
    if inscricao_evento is None:
        return HttpResponseForbidden("Você precisa estar inscrito no evento primeiro.")

    # RN1: Capacidade da sala calculada dinamicamente
    ocupadas = InscricaoAtividade.objects.filter(atividade=atividade).count()
    if ocupadas >= atividade.sala.capacidade:
        messages.error(request, "Esta atividade está lotada.")
        return redirect("detalhe_evento", pk=atividade.evento_id)

    if InscricaoAtividade.objects.filter(inscricao_evento=inscricao_evento, atividade=atividade).exists():
        messages.error(request, "Você já está inscrito nesta atividade.")
        return redirect("detalhe_evento", pk=atividade.evento_id)

    # RN2: Conflito de agenda do participante (considera todos os eventos)
    conflito = Atividade.objects.filter(
        inscricoes__inscricao_evento__participante=request.user,
        inicio__lt=atividade.fim,
        fim__gt=atividade.inicio,
    ).exists()

    if conflito:
        messages.error(request, "Esta atividade conflita com outra em que você já está inscrito.")
        return redirect("detalhe_evento", pk=atividade.evento_id)

    InscricaoAtividade.objects.create(inscricao_evento=inscricao_evento, atividade=atividade)
    return redirect("detalhe_evento", pk=atividade.evento_id)


# --- CANCELAMENTOS ---
class ApenasDonoInscricaoAtividadeMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        self.inscricao = get_object_or_404(InscricaoAtividade, pk=kwargs["pk"])
        if self.inscricao.inscricao_evento.participante_id != request.user.pk:
            return HttpResponseForbidden("Você só pode cancelar suas próprias inscrições.")
        return super().dispatch(request, *args, **kwargs)


class CancelarAtividadeView(ApenasDonoInscricaoAtividadeMixin, View):
    def post(self, request, pk):
        evento_id = self.inscricao.atividade.evento_id
        self.inscricao.delete()
        return redirect("detalhe_evento", pk=evento_id)


class ApenasDonoInscricaoEventoMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        self.inscricao = get_object_or_404(InscricaoEvento, pk=kwargs["pk"])
        if self.inscricao.participante_id != request.user.pk:
            return HttpResponseForbidden("Você só pode cancelar sua própria inscrição.")
        return super().dispatch(request, *args, **kwargs)


class CancelarEventoView(ApenasDonoInscricaoEventoMixin, View):
    def post(self, request, pk):
        evento_id = self.inscricao.evento_id
        self.inscricao.delete()  # RN5: CASCADE remove automaticamente as atividades
        return redirect("detalhe_evento", pk=evento_id)


# --- AGENDA E PAINEL ---
@login_required
def minha_agenda(request):
    inscricoes = InscricaoAtividade.objects.filter(
        inscricao_evento__participante=request.user
    ).select_related("atividade", "atividade__sala", "atividade__evento").order_by("atividade__inicio")
    return render(request, "inscricoes/minha_agenda.html", {"inscricoes": inscricoes})


@dono_do_evento_required
def painel_organizador(request, pk):
    evento = request.evento
    atividades = evento.atividades.prefetch_related("inscricoes__inscricao_evento__participante")
    return render(request, "inscricoes/painel_organizador.html", {"evento": evento, "atividades": atividades})