from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from .models import Resource
from .forms import ResourceUploadForm

@login_required
def index(request):
    resources = Resource.objects.all().order_by('-created_at')
    return render(request, 'resources/index.html', {'resources': resources})

@login_required
def upload_resource(request):
    if not (request.user.is_staff or request.user.is_superuser or hasattr(request.user, 'mentor')):
        messages.error(request, "You are not authorized to upload resources.")
        return redirect('resources:index')

    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploader = request.user
            resource.save()
            messages.success(request, "Resource uploaded successfully!")
            return redirect('resources:index')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ResourceUploadForm()
    return render(request, 'resources/upload_resource.html', {'form': form})

@login_required
def download_resource(request, pk):
    resource = get_object_or_404(Resource, pk=pk)
    if resource.file:
        resource.download_count += 1
        resource.save()
        try:
            return FileResponse(resource.file.open('rb'), as_attachment=True, filename=resource.file.name.split('/')[-1])
        except FileNotFoundError:
            raise Http404("File not found.")
    else:
        messages.error(request, "No file associated with this resource.")
        return redirect('resources:index')