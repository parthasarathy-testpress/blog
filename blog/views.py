from django.shortcuts import get_object_or_404, render
from django.core.mail import send_mail

from django.views.generic import ListView, DetailView
from .models import Post

from .forms import EmailPostForm,CommentForm

from taggit.models import Tag

class PostListView(ListView):
    model = Post
    template_name = 'blog/post/list.html'
    context_object_name = 'posts'
    paginate_by = 3
    def get_queryset(self):
        queryset = Post.objects.all()
        tag_slug = self.kwargs.get('tag_slug')
        if tag_slug:
            self.tag = get_object_or_404(Tag, slug=tag_slug)
            queryset = queryset.filter(tags__in=[self.tag])
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = getattr(self, 'tag', None)
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post/detail.html'
    context_object_name = 'post'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Post,
            slug=self.kwargs['post'],
            status='published',
            publish__year=self.kwargs['year'],
            publish__month=self.kwargs['month'],
            publish__day=self.kwargs['day']
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.object.comments.filter(active=True)
        context['new_comment'] = None
        context['comment_form'] = CommentForm()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        comments = self.object.comments.filter(active=True)
        new_comment = None
        
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.post = self.object
            new_comment.save()
        
        return render(request, 'blog/post/detail.html', {
            'post': self.object,
            'comments': comments,
            'new_comment': new_comment,
            'comment_form': comment_form
        })
    


def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
      form = EmailPostForm(request.POST)
      if form.is_valid():
        cd = form.cleaned_data
        post_url = request.build_absolute_uri(post.get_absolute_url())
        subject = f"{cd['name']} recommends you read {post.title}"
        message = f"Read {post.title} at {post_url}\n\n {cd['name']}\'s comments: {cd['comments']}"
        send_mail(subject, message, 'admin@myblog.com', [cd['to']])
        sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'post': post, 'form': form, 'sent': sent})

