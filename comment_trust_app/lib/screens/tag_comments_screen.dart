import 'package:flutter/material.dart';
import '../route/api_config.dart';
import '../services/tag_service.dart';

class TagCommentsScreen extends StatefulWidget {
  final String productKey;
  final String tag;
  const TagCommentsScreen({super.key, required this.productKey, required this.tag});

  @override
  State<TagCommentsScreen> createState() => _TagCommentsScreenState();
}

class _TagCommentsScreenState extends State<TagCommentsScreen> {
  bool _loading = true;
  List<Map<String,dynamic>> _comments = [];

  @override
  void initState() {
    super.initState();
    _fetch();
  }

  Future<void> _fetch() async {
    await ApiConfig.I.load();
    if (ApiConfig.I.demoMode || widget.productKey.isEmpty) {
      setState(()=> _loading = false);
      return;
    }
    final data = await TagService.fetchCommentsByTag(ApiConfig.I.baseUrl, widget.productKey, widget.tag);
    print('[TagCommentsScreen] Fetched ${data.length} comments for tag=${widget.tag}, sample: ${data.isNotEmpty ? data.take(3).toList() : []}');
    if (!mounted) return;
    setState(() { _comments = data; _loading = false; });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        backgroundColor: const Color(0xFF1B4D3E),
        elevation: 0,
        title: Row(children:[
          Container(width:24,height:24,decoration:BoxDecoration(color:Colors.white,borderRadius:BorderRadius.circular(4)),child:const Icon(Icons.tag,color:Color(0xFF1B4D3E),size:16)),
          const SizedBox(width:8),
          Text('Tag: ${widget.tag}', style: const TextStyle(color:Colors.white,fontSize:16,fontWeight:FontWeight.w500)),
        ]),
      ),
      body: _loading ? const Center(child: CircularProgressIndicator()) : ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: _comments.length,
        itemBuilder: (ctx,i){
          final c = _comments[i];
          final username = c['user_name'] ?? c['username'] ?? 'Anon';
          final text = c['text'] ?? c['comment'] ?? '';
          final tags = (c['tags'] as List?) ?? [];
          return Container(
            margin: const EdgeInsets.only(bottom:12),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(color:Colors.white,borderRadius:BorderRadius.circular(10),boxShadow:[BoxShadow(color:Color.fromRGBO(0,0,0,0.05),blurRadius:8,offset:const Offset(0,2))]),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start,children:[
              Row(children:[
                CircleAvatar(radius:20,backgroundColor:Colors.grey[300],child:const Icon(Icons.person,color:Colors.grey,size:20)),
                const SizedBox(width:12),
                Expanded(child: Text(username, style: const TextStyle(fontSize:14,fontWeight:FontWeight.w600,color:Colors.black87))),
              ]),
              const SizedBox(height:10),
              Text(text, style: const TextStyle(fontSize:12,color:Colors.black87,height:1.4)),
              if(tags.isNotEmpty) ...[
                const SizedBox(height:8),
                Wrap(spacing:6,runSpacing:6,children:[for(final t in tags) _tagChip(t.toString())]),
              ]
            ]),
          );
        },
      ),
    );
  }

  Widget _tagChip(String tag){
    return Container(
      padding: const EdgeInsets.symmetric(horizontal:10,vertical:5),
      decoration: BoxDecoration(color:const Color(0xFF1B4D3E),borderRadius:BorderRadius.circular(14)),
      child: Text(tag, style: const TextStyle(color:Colors.white,fontSize:11,fontWeight:FontWeight.w500)),
    );
  }

}
