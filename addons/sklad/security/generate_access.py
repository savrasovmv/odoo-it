

spisok = []
spisok.append(['sklad.sklad','', 1])
spisok.append(['sklad.location','', 1])
spisok.append(['sklad.assets','', 1])
spisok.append(['sklad.assets_category','', 1])
spisok.append(['sklad.product_uom','', 1])
spisok.append(['sklad.product_category','', 1])
spisok.append(['sklad.product','', 1])
spisok.append(['sklad.transfer_use','', 1])
spisok.append(['sklad.transfer_use_assets_line','', 1])
spisok.append(['sklad.transfer_use_product_line','', 1])


print("id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink")
for name in spisok:
	class_name = name[0].replace('.','_')
	modul_name = ''
	
	if len(name[1])>0:
		modul_name = name[1] + '.'
	print('access_%(class_name)s_manager,%(name)s,%(modul_name)smodel_%(class_name)s,sklad.group_sklad_manager,1,1,1,1' % {'name':name[0], 'class_name': class_name, 'modul_name': modul_name})
	if name[2]>0:
		print('access_%(class_name)s_users,%(name)s,%(modul_name)smodel_%(class_name)s,sklad.group_sklad_read_only,1,0,0,0'  % {'name':name[0], 'class_name': class_name, 'modul_name': modul_name})


# Для пользователя
spisok = []
spisok.append(['sklad.transfer_use','', 1])
spisok.append(['sklad.transfer_use_assets_line','', 1])
spisok.append(['sklad.transfer_use_product_line','', 1])

for name in spisok:
	class_name = name[0].replace('.','_')
	modul_name = ''
	
	if len(name[1])>0:
		modul_name = name[1] + '.'
	
	print('access_%(class_name)s_users,%(name)s,%(modul_name)smodel_%(class_name)s,sklad.group_sklad_user,1,1,1,0'  % {'name':name[0], 'class_name': class_name, 'modul_name': modul_name})
	
