# Flutter Implementation Guide for College Community API

## Quick Start
Use this with your AI agent to generate a complete Flutter app for the College Community API.

## Project Structure
```
lib/
├── main.dart
├── models/
│   ├── user.dart
│   ├── post.dart
│   └── api_response.dart
├── services/
│   ├── api_service.dart
│   ├── auth_service.dart
│   └── storage_service.dart
├── screens/
│   ├── login_screen.dart
│   ├── feed_screen.dart
│   ├── create_post_screen.dart
│   ├── profile_screen.dart
│   └── post_detail_screen.dart
├── widgets/
│   ├── post_card.dart
│   ├── post_type_badge.dart
│   └── engagement_row.dart
└── utils/
    ├── constants.dart
    └── helpers.dart
```

## Required Dependencies (pubspec.yaml)
```yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0                    # API calls
  flutter_secure_storage: ^9.0.0 # JWT storage
  provider: ^6.1.1               # State management
  image_picker: ^1.0.4           # Post images
  cached_network_image: ^3.3.0   # Image caching
  intl: ^0.18.1                  # Date formatting
  pull_to_refresh: ^2.0.0        # Refresh functionality
```

## API Service Implementation
```dart
// services/api_service.dart
class ApiService {
  static const String baseUrl = 'http://localhost:8000';
  
  // Headers with JWT
  Map<String, String> _getHeaders() {
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer ${AuthService.getToken()}',
    };
  }
  
  // Login
  Future<AuthResponse> login(String username, String password) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'username': username,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      return AuthResponse.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Login failed');
    }
  }
  
  // Get Posts with Pagination
  Future<List<Post>> getPosts({int skip = 0, int limit = 20}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/posts/?skip=$skip&limit=$limit'),
      headers: _getHeaders(),
    );
    
    if (response.statusCode == 200) {
      List<dynamic> jsonList = jsonDecode(response.body);
      return jsonList.map((json) => Post.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load posts');
    }
  }
  
  // Create Post
  Future<Post> createPost({
    required String title,
    required String content,
    String? imageUrl,
    String postType = 'GENERAL',
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/posts/'),
      headers: _getHeaders(),
      body: jsonEncode({
        'title': title,
        'content': content,
        'image_url': imageUrl,
        'post_type': postType,
      }),
    );
    
    if (response.statusCode == 200) {
      return Post.fromJson(jsonDecode(response.body));
    } else {
      throw Exception('Failed to create post');
    }
  }
  
  // Like Post
  Future<void> likePost(int postId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/posts/$postId/like'),
      headers: _getHeaders(),
    );
    
    if (response.statusCode != 200) {
      throw Exception('Failed to like post');
    }
  }
}
```

## Data Models
```dart
// models/user.dart
class User {
  final int id;
  final String username;
  final String email;
  final String fullName;
  final String department;
  final String className;
  final String academicYear;
  final int collegeId;
  final String collegeName;
  final String collegeSlug;
  final DateTime createdAt;
  final DateTime updatedAt;

  User({...}); // Constructor
  
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'],
      username: json['username'],
      email: json['email'],
      fullName: json['full_name'],
      department: json['department'],
      className: json['class_name'],
      academicYear: json['academic_year'],
      collegeId: json['college_id'],
      collegeName: json['college_name'],
      collegeSlug: json['college_slug'],
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
    );
  }
}

// models/post.dart
class Post {
  final int id;
  final String title;
  final String content;
  final String? imageUrl;
  final String postType;
  final int authorId;
  final int collegeId;
  final PostMetadata metadata;
  final DateTime createdAt;
  final DateTime updatedAt;
  final String authorName;
  final String authorDepartment;
  final String timeAgo;

  Post({...}); // Constructor
  
  factory Post.fromJson(Map<String, dynamic> json) {
    return Post(
      id: json['id'],
      title: json['title'],
      content: json['content'],
      imageUrl: json['image_url'],
      postType: json['post_type'],
      authorId: json['author_id'],
      collegeId: json['college_id'],
      metadata: PostMetadata.fromJson(json['post_metadata']),
      createdAt: DateTime.parse(json['created_at']),
      updatedAt: DateTime.parse(json['updated_at']),
      authorName: json['author_name'],
      authorDepartment: json['author_department'],
      timeAgo: json['time_ago'],
    );
  }
}

class PostMetadata {
  final int likes;
  final int comments;
  final int shares;
  
  PostMetadata({
    required this.likes,
    required this.comments,
    required this.shares,
  });
  
  factory PostMetadata.fromJson(Map<String, dynamic> json) {
    return PostMetadata(
      likes: json['likes'] ?? 0,
      comments: json['comments'] ?? 0,
      shares: json['shares'] ?? 0,
    );
  }
}
```

## Key Widgets
```dart
// widgets/post_card.dart
class PostCard extends StatelessWidget {
  final Post post;
  final VoidCallback? onLike;
  final VoidCallback? onTap;
  
  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(8.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header with author info and post type badge
          ListTile(
            leading: CircleAvatar(
              child: Text(post.authorName[0]),
            ),
            title: Text(post.authorName),
            subtitle: Text('${post.authorDepartment} • ${post.timeAgo}'),
            trailing: PostTypeBadge(postType: post.postType),
          ),
          
          // Post content
          Padding(
            padding: EdgeInsets.all(16.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  post.title,
                  style: Theme.of(context).textTheme.headlineSmall,
                ),
                SizedBox(height: 8),
                Text(post.content),
                
                // Image if available
                if (post.imageUrl != null) ...[
                  SizedBox(height: 12),
                  CachedNetworkImage(
                    imageUrl: post.imageUrl!,
                    width: double.infinity,
                    fit: BoxFit.cover,
                    placeholder: (context, url) => CircularProgressIndicator(),
                    errorWidget: (context, url, error) => Icon(Icons.error),
                  ),
                ],
              ],
            ),
          ),
          
          // Engagement row
          EngagementRow(
            metadata: post.metadata,
            onLike: onLike,
          ),
        ],
      ),
    );
  }
}

// widgets/post_type_badge.dart
class PostTypeBadge extends StatelessWidget {
  final String postType;
  
  @override
  Widget build(BuildContext context) {
    Color color;
    switch (postType) {
      case 'IMPORTANT':
        color = Colors.red;
        break;
      case 'ANNOUNCEMENT':
        color = Colors.blue;
        break;
      case 'INFO':
        color = Colors.orange;
        break;
      default:
        color = Colors.grey;
    }
    
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        postType,
        style: TextStyle(
          color: Colors.white,
          fontSize: 12,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }
}

// widgets/engagement_row.dart
class EngagementRow extends StatelessWidget {
  final PostMetadata metadata;
  final VoidCallback? onLike;
  
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        IconButton(
          icon: Icon(Icons.favorite_border),
          onPressed: onLike,
        ),
        Text('${metadata.likes}'),
        SizedBox(width: 16),
        Icon(Icons.comment_outlined),
        Text('${metadata.comments}'),
        SizedBox(width: 16),
        Icon(Icons.share_outlined),
        Text('${metadata.shares}'),
      ],
    );
  }
}
```

## Screen Examples
```dart
// screens/feed_screen.dart
class FeedScreen extends StatefulWidget {
  @override
  _FeedScreenState createState() => _FeedScreenState();
}

class _FeedScreenState extends State<FeedScreen> {
  List<Post> posts = [];
  int currentPage = 0;
  bool isLoading = false;
  
  @override
  void initState() {
    super.initState();
    _loadPosts();
  }
  
  Future<void> _loadPosts({bool refresh = false}) async {
    if (isLoading) return;
    
    setState(() {
      isLoading = true;
      if (refresh) {
        posts.clear();
        currentPage = 0;
      }
    });
    
    try {
      List<Post> newPosts = await ApiService().getPosts(
        skip: currentPage * 20,
        limit: 20,
      );
      
      setState(() {
        if (refresh) {
          posts = newPosts;
        } else {
          posts.addAll(newPosts);
        }
        currentPage++;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load posts: $e')),
      );
    } finally {
      setState(() {
        isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('College Community'),
        actions: [
          IconButton(
            icon: Icon(Icons.add),
            onPressed: () => Navigator.pushNamed(context, '/create-post'),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => _loadPosts(refresh: true),
        child: ListView.builder(
          itemCount: posts.length + (isLoading ? 1 : 0),
          itemBuilder: (context, index) {
            if (index >= posts.length) {
              return Center(child: CircularProgressIndicator());
            }
            
            return PostCard(
              post: posts[index],
              onLike: () => _likePost(posts[index].id),
              onTap: () => Navigator.pushNamed(
                context,
                '/post-detail',
                arguments: posts[index],
              ),
            );
          },
        ),
      ),
    );
  }
  
  Future<void> _likePost(int postId) async {
    try {
      await ApiService().likePost(postId);
      // Refresh the post to get updated like count
      _loadPosts(refresh: true);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to like post')),
      );
    }
  }
}
```

## Authentication Flow
```dart
// services/auth_service.dart
class AuthService {
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'jwt_token';
  
  static Future<void> saveToken(String token) async {
    await _storage.write(key: _tokenKey, value: token);
  }
  
  static Future<String?> getToken() async {
    return await _storage.read(key: _tokenKey);
  }
  
  static Future<void> deleteToken() async {
    await _storage.delete(key: _tokenKey);
  }
  
  static Future<bool> isLoggedIn() async {
    final token = await getToken();
    return token != null;
  }
}
```

## Testing Instructions
1. **Start the API server**: `docker compose up`
2. **Test credentials**: username: `john_doe`, password: `password123`
3. **API endpoint**: `http://localhost:8000`
4. **Test the login flow first**
5. **Test post creation and engagement features**

## UI/UX Guidelines
- **Post Priority Colors**: Important=Red, Announcement=Blue, Info=Yellow, General=Gray
- **Infinite Scroll**: Load 20 posts per page
- **Pull-to-Refresh**: Refresh entire feed
- **Image Display**: Use cached_network_image for performance
- **Time Display**: Show relative time (e.g., "2 minutes ago")
- **Multi-tenant**: Only show posts from user's college

This guide provides everything needed for an AI agent to create a complete Flutter app! 🚀