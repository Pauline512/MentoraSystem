from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import FileResponse, Http404
from .models import Resource
from .forms import ResourceUploadForm

@login_required
def index(request):
    resources = Resource.objects.all().order_by('-created_at')
    print(dir(request.user))
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
    
    
@login_required
def edit_resource(request, pk):
    """
    Allows an authorized user to edit an existing resource.
    """
    # Get the specific resource object, or return a 404 error if not found
    resource = get_object_or_404(Resource, pk=pk)

    # --- Authorization Check ---
    # Check if the current user is the original uploader OR if they are staff/admin.
    # This prevents users from editing resources they don't own.
    if not (resource.uploader == request.user or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You are not authorized to edit this resource.")
        return redirect('resources:index')

    # If the request is a POST, it means the form has been submitted
    if request.method == 'POST':
        # Populate the form with the submitted data (request.POST) and files (request.FILES),
        # and link it to the existing resource instance.
        form = ResourceUploadForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save() # Save the changes to the database
            messages.success(request, f"'{resource.title}' has been updated successfully!")
            return redirect('resources:index')
        else:
            messages.error(request, "Please correct the errors below.")
    
    # If the request is a GET, it means the user is just visiting the edit page
    else:
        # Populate the form with the existing data from the 'resource' object
        form = ResourceUploadForm(instance=resource)

    # Render the edit page template, passing the form and resource object
    # to the template context.
    context = {
        'form': form,
        'resource': resource
    }
    return render(request, 'resources/edit_resource.html', context)
    