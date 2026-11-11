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
from django.core.exceptions import ValidationError
from django.db.models import Count
from . import services

# --- AUTENTICAÇÃO ---
class CadastroView(CreateView):
    form_class = UserCreationForm
    template_name = "registration/cadastro.html"
    success_url = reverse_lazy("lista_eventos")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)  # Loga o utilizador automaticamente
        return response


eh_organizador = services.eh_organizador


def dono_do_evento_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        evento = get_object_or_404(Evento, pk=kwargs["pk"])
        services.exigir_dono_evento(request.user, evento)
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
    evento = get_object_or_404(Evento.objects.select_related("organizador"), pk=pk)
    atividades = evento.atividades.select_related("sala").annotate(total_inscritos=Count("inscricoes"))
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
    return formulario_atividade(request, request.evento, Atividade(evento=request.evento))


@dono_do_evento_required
def editar_atividade(request, pk, atividade_pk):
    atividade = get_object_or_404(Atividade, pk=atividade_pk, evento=request.evento)
    return formulario_atividade(request, request.evento, atividade)


def formulario_atividade(request, evento, atividade):
    form = AtividadeForm(request.POST or None, instance=atividade)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('detalhe_evento', pk=evento.pk)
    return render(request, 'inscricoes/form_atividade.html', {'form': form})


# --- INSCRIÇÕES ---
@login_required
def inscrever_evento(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    evento = get_object_or_404(Evento, pk=pk)
    try:
        services.inscrever_evento(request.user, evento)
        messages.success(request, 'Inscrição no evento realizada.')
    except ValidationError as erro:
        messages.error(request, '; '.join(erro.messages))
    return redirect('detalhe_evento', pk=pk)  # POST_REDIRECT


@login_required
def inscrever_atividade(request, pk):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    atividade = get_object_or_404(Atividade, pk=pk)
    try:
        services.inscrever_atividade(request.user, atividade)
        messages.success(request, 'Inscrição na atividade realizada.')
    except ValidationError as erro:
        if not InscricaoEvento.objects.filter(evento=atividade.evento, participante=request.user).exists():
            return HttpResponseForbidden('; '.join(erro.messages))
        messages.error(request, '; '.join(erro.messages))
    return redirect('detalhe_evento', pk=atividade.evento_id)


class CancelamentoView(LoginRequiredMixin, View):
    model = None

    def post(self, request, pk):
        inscricao = get_object_or_404(self.model, pk=pk)
        evento_id = inscricao.evento_id if isinstance(inscricao, InscricaoEvento) else inscricao.atividade.evento_id
        services.cancelar(request.user, inscricao)
        messages.success(request, 'Inscrição cancelada.')
        return redirect('detalhe_evento', pk=evento_id)


class CancelarAtividadeView(CancelamentoView):
    model = InscricaoAtividade


class CancelarEventoView(CancelamentoView):
    model = InscricaoEvento


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