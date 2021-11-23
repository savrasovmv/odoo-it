spisok = []
spisok.append(['ad.ou',''])
spisok.append(['ad.department',''])
spisok.append(['ad.group',''])
spisok.append(['ad.users',''])
spisok.append(['ad.users_group_line',''])
spisok.append(['ad.set_group',''])
spisok.append(['ad.set_group_line',''])
spisok.append(['jms.event_log',''])
spisok.append(['jms.wizard',''])
spisok.append(['jms.report',''])



spisok_read = []
spisok_read.append(['krs.struktura',''])






print("id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink")
for name in spisok:
	class_name = name[0].replace('.','_')
	modul_name = ''
	
	if len(name[1])>0:
		modul_name = name[1] + '.'
	print('access_%(class_name)s_manager,%(name)s,%(modul_name)smodel_%(class_name)s,group_ad_manager,1,1,1,1' % {'name':name[0], 'class_name': class_name, 'modul_name': modul_name})
	print('access_%(class_name)s_users,%(name)s,%(modul_name)smodel_%(class_name)s,group_ad_users,1,0,0,0'  % {'name':name[0], 'class_name': class_name, 'modul_name': modul_name})
